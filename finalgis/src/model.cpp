// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 Finalverse contributors.
#include "geography.hpp"
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QTimer>
#include <QUrl>
#include <QFileInfo>
#include <QJsonDocument>
#include <QElapsedTimer>
#include <sys/stat.h>
#include <unistd.h>

namespace {
QUrl checked(const QString &endpoint,bool allowRemote) {
 QUrl u(endpoint);const bool local=QStringList{"127.0.0.1","localhost","::1"}.contains(u.host());
 if(!u.isValid()||u.host().isEmpty()||!u.userInfo().isEmpty()||u.hasQuery()||u.hasFragment()||(!local&&!allowRemote)||(u.scheme()!="https"&&!(local&&u.scheme()=="http")))fgis::fail("Network endpoint requires HTTPS and explicit remote permission, or local loopback HTTP");
 return u;
}
QByteArray request(const QUrl &url,const QByteArray &payload,const QString &keyFile={}) {
 QNetworkAccessManager manager;QNetworkRequest req(url);req.setHeader(QNetworkRequest::ContentTypeHeader,"application/json");
 req.setAttribute(QNetworkRequest::RedirectPolicyAttribute,QNetworkRequest::ManualRedirectPolicy);
 if(!keyFile.isEmpty()){
  struct stat st{};if(lstat(keyFile.toUtf8().constData(),&st)||!S_ISREG(st.st_mode)||st.st_uid!=getuid()||(st.st_mode&077)!=0)fgis::fail("API key requires an owned private regular file");
  auto key=fgis::read(keyFile,4096).trimmed();if(key.isEmpty()||key.contains('\r')||key.contains('\n')||key.contains('\0'))fgis::fail("Invalid key file");req.setRawHeader("Authorization","Bearer "+key);
 }
 QEventLoop loop;QTimer timer;timer.setSingleShot(true);bool timeout=false,oversized=false;QByteArray data;
 auto *reply=payload.isEmpty()?manager.get(req):manager.post(req,payload);
 QObject::connect(reply,&QIODevice::readyRead,[&](){data+=reply->read(65537-data.size());if(data.size()>65536){oversized=true;reply->abort();}});
 QObject::connect(&timer,&QTimer::timeout,[&](){timeout=true;reply->abort();loop.quit();});
 QObject::connect(reply,&QNetworkReply::finished,&loop,&QEventLoop::quit);timer.start(30000);loop.exec();timer.stop();
 data+=reply->read(65537-data.size());const auto error=reply->error();const int status=reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();delete reply;
 if(timeout)fgis::fail("Model request timed out after 30 seconds");
 if(oversized||data.size()>65536)fgis::fail("Model response exceeded 64 KiB");
 if(error!=QNetworkReply::NoError||status!=200)fgis::fail("Model provider HTTP/transport failure");return data;
}
}
namespace fgis {
QJsonObject discover(const QString &endpoint,bool allowRemote) {
 auto u=checked(endpoint,allowRemote);u.setPath(u.path().remove(QRegularExpression("/$"))+"/api/tags");
 const auto result=object(request(u,{}));QJsonArray models;
 for(const auto &m:result.value("models").toArray()){if(models.size()>=64)break;auto name=m.toObject().value("name").toString();if(!name.isEmpty()&&name.size()<=128)models.append(name);}
 return {{"provider","ollama"},{"models",models},{"capabilities",QJsonArray{"structured_plan","local_only_default","30s_timeout","64KiB_response_cap","128_token_generation_cap"}}};
}
QJsonObject modelPlan(const QString &userRequest,const QString &provider,const QString &model,const QString &endpoint,const QString &keyFile,bool allowRemote) {
 auto baseline=plan(userRequest);QElapsedTimer time;time.start();
 QJsonObject receipt{{"provider",provider},{"model",model},{"request_sha256",sha(userRequest.toUtf8())},{"max_tokens",128},{"timeout_ms",30000},{"remote_authorized",allowRemote},{"dataset_transmitted",false}};
 if(provider=="mock"){receipt["model"]=QJsonValue();receipt["outcome"]="deterministic_mock";baseline["planning"]=receipt;return baseline;}
 if(provider!="ollama"&&provider!="openai")fail("Unknown provider");
 if(model.isEmpty()||model.size()>128)fail("Invalid model name");
 // Validate permissions before fallback; a denied endpoint is a request error.
 auto url=checked(endpoint,allowRemote);
 const auto prompt=QString("You select a reviewed GIS recipe. Return only JSON {\"recipe\":\"montreal_roads_buildings_v1\"}. This recipe inspects public roof/road/DEM data, projects to EPSG:2950, clips a 260m square and generates estimated building massing. If request is unrelated return {\"recipe\":\"unsupported\"}. User intent: ")+userRequest;
 QJsonObject payload;
 if(provider=="ollama") {url.setPath("/api/generate");payload={{"model",model},{"prompt",prompt},{"stream",false},{"format","json"},{"options",QJsonObject{{"temperature",0},{"seed",0},{"num_predict",128},{"num_ctx",1024}}}};}
 else {url.setPath(url.path().remove(QRegularExpression("/$"))+"/chat/completions");payload={{"model",model},{"messages",QJsonArray{QJsonObject{{"role","user"},{"content",prompt}}}},{"max_tokens",128},{"temperature",0}};}
 try {
  const auto raw=request(url,QJsonDocument(payload).toJson(QJsonDocument::Compact),keyFile);auto body=object(raw);QString response;
  if(provider=="ollama")response=body.value("response").toString();
  else {auto choices=body.value("choices").toArray();if(!choices.isEmpty())response=choices[0].toObject().value("message").toObject().value("content").toString();}
  auto proposal=object(response.toUtf8());if(proposal.size()!=1||proposal.value("recipe")!="montreal_roads_buildings_v1")fail("Provider did not select an admitted recipe");
  receipt["outcome"]="validated_model_recipe";receipt["response_sha256"]=sha(raw);receipt["proposal"]=proposal;
 }catch(const std::exception &e){receipt["outcome"]="deterministic_fallback";receipt["failure"]=e.what();}
 receipt["elapsed_ms"]=double(time.nsecsElapsed())/1e6;baseline["planning"]=receipt;validatePlan(baseline);return baseline;
}
}
