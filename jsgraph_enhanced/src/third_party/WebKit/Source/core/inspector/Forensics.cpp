#include "core/inspector/Forensics.h"

#include "core/page/ChromeClient.h"
#include "core/dom/Node.h"
#include "core/dom/Element.h"
#include "core/dom/events/Event.h"
#include "core/html/HTMLScriptElement.h"
#include "core/editing/serializers/Serialization.h"
#include "core/page/Page.h"
#include "core/frame/LocalFrame.h"
#include "core/dom/ExecutionContext.h"
#include "core/html_names.h"

#include "platform/weborigin/KURL.h"
#include "platform/wtf/text/WTFString.h"
#include "platform/wtf/text/TextPosition.h"

#include "public/web/WebWindowFeatures.h"
#include "public/platform/Platform.h"
#include "public/platform/WebThread.h"
#include "base/memory/scoped_refptr.h"
#include "base/logging.h"

#include "core/inspector/ForensicsV8EventListener.h"
#include "content/public/renderer/v8_value_converter.h"
#include "base/json/json_string_value_serializer.h"
#include "bindings/core/v8/V8CrossOriginSetterInfo.h"
#include "bindings/core/v8/ScriptSourceCode.h"
#include "core/frame/LocalDOMWindow.h"
#include "bindings/core/v8/serialization/SerializedScriptValue.h"

#include <sstream>

#define _IFA_DISABLE_ // return;

#define _IFAC_ "LOG::Forensics"
#define _IFAF_ __func__
#define _IFA_LOG_SPACE_ "\n  -*#$"
#define _IFA_ANDROID_LOGCAT_

#define _IFA_LOG_PREFIX_  _IFAC_ << "::" << _IFAF_ << " :"
#define _IFA_LOG_SUFFIX_  "\n---***###$$$\n"


#define _IFA_LOG_FRAME_  _IFA_LOG_SPACE_ << "frame=" << frame \
          << _IFA_LOG_SPACE_ << "frame_url=" \
              << GetDocumentURL(frame).Utf8().data() \
          << _IFA_LOG_SPACE_ << "main_frame=" << GetMainFrame(frame) \
          << _IFA_LOG_SPACE_ << "local_frame_root=" \
              << GetFrameRoot(frame) \
          << _IFA_LOG_SPACE_ << "local_frame_root_url=" \
              << GetFrameRootURL(frame) \
          << _IFA_LOG_SPACE_ << "document=" << (void*)GetDocument(frame)

namespace blink {

using std::string;

//static
Document* Forensics::GetDocument(LocalFrame* frame) {
  if(!frame)
      return nullptr;

  return frame->GetDocument();
}

//static
String Forensics::GetDocumentURL(LocalFrame* frame) {
  if(!frame || !frame->GetDocument())
      return KURL().GetString();

  return frame->GetDocument()->Url().GetString();
}

//static
LocalFrame* Forensics::GetFrameRoot(LocalFrame* frame) {
  if(!frame)
      return nullptr;

  return &(frame->LocalFrameRoot());
}

//static
String Forensics::GetFrameRootURL(LocalFrame* frame) {
  if(!frame)
      return KURL().GetString();

  return GetDocumentURL(GetFrameRoot(frame));
}

//static
Frame* Forensics::GetMainFrame(LocalFrame* frame) {
  if(!frame || !frame->GetDocument() || !frame->GetDocument()->GetPage())
      return nullptr;

  return frame->GetDocument()->GetPage()->MainFrame();
}

//static
ChromeClient* Forensics::GetChromeClient(LocalFrame* frame) {
  if(!frame || !frame->GetDocument() || !frame->GetDocument()->GetPage())
    return nullptr;
  
  return &(frame->GetDocument()->GetPage()->GetChromeClient());
}

//static
void Forensics::LogInfo(std::string log_str) {
  // Write log that can be read via adb logcat
  LOG(INFO) << log_str;
}

//static
bool Forensics::IsWhitespace(Node* node) {
  // TODO: pull ignoreWhitespace setting from the frontend and use here.
  return node && node->getNodeType() == Node::kTextNode &&
         node->nodeValue().StripWhiteSpace().length() == 0;
}

void Forensics::DidInsertDOMNode(Node* node) {

  _IFA_DISABLE_

  if (IsWhitespace(node))
    return;

  if(!node || !node->GetDocument().GetFrame())
    return;

  LocalFrame* frame = node->GetDocument().GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "parent_ptr=" << (void*)(node->parentNode())
          << _IFA_LOG_SPACE_ << "prev_sibling_ptr=" << (void*)(node->previousSibling())
          << _IFA_LOG_SPACE_ << "next_sibling_ptr=" << (void*)(node->nextSibling())
          << _IFA_LOG_SPACE_ << "node_ptr=" << (void*)node
          << _IFA_LOG_SPACE_ << "node=" << node;
  
  Element* element = nullptr; 
  if(node->IsHTMLElement())
    // element = dynamic_cast<Element*>(node);
    element = (Element*)node;

  if(!element) {
    log_str << _IFA_LOG_SUFFIX_;
    LogInfo(log_str.str());
    return;
  }

  if(element->IsLink()) {
    log_str << _IFA_LOG_SPACE_ << "node_href=" 
            << element->HrefURL().GetString().Utf8().data();
  }
  else if(element->IsScriptElement()) {
    String src_attr = element->getAttribute(HTMLNames::srcAttr).GetString();
    log_str << _IFA_LOG_SPACE_ << "src_url=" << src_attr.Utf8().data();
  }

  log_str << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::WillRemoveDOMNode(Node* node) {

  _IFA_DISABLE_

  if (IsWhitespace(node))
    return;
  
  if(!node || !node->GetDocument().GetFrame())
    return;

  LocalFrame* frame = node->GetDocument().GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "parent_ptr=" << (void*)(node->parentNode())
          << _IFA_LOG_SPACE_ << "prev_sibling_ptr=" << (void*)(node->previousSibling())
          << _IFA_LOG_SPACE_ << "next_sibling_ptr=" << (void*)(node->nextSibling())
          << _IFA_LOG_SPACE_ << "node_ptr=" << (void*)node
          << _IFA_LOG_SPACE_ << "node=" << node
          << _IFA_LOG_SUFFIX_;
  // TODO(Roberto): add full markup?
  LogInfo(log_str.str());
}


void Forensics::DidCreateChildFrame(LocalFrame* frame,
                                    LocalFrame* child_frame,
                                    const char* child_name,
                                    Node* owner_element) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_ 
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "child_frame=" << child_frame
          << _IFA_LOG_SPACE_ << "child_name=" << child_name
          << _IFA_LOG_SPACE_ << "owner_element=" << (void*)owner_element 
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::WindowCreated(LocalFrame* created) {

  LocalFrame* frame = created;

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_  
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "created_frame=" << created
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::WindowOpen(Document* document,
                            const String& url,
                            const AtomicString& window_name,
                            const WebWindowFeatures& window_features,
                            bool user_gesture) {

  LocalFrame* frame = document->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_ 
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "url=" << url.Utf8().data()
          << _IFA_LOG_SPACE_ << "name=" << window_name.GetString().Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::LoadEventFired(LocalFrame* frame) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_ 
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}
// static

void Forensics::DidCreateDocumentLoader(LocalFrame* frame, 
                                           const KURL& url, 
                                           FrameLoadType load_type, 
                                           NavigationType navigation_type) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "load_url=" << url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "frame_load_type=" << load_type
          << _IFA_LOG_SPACE_ << "navigation_type=" << navigation_type
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

// static
void Forensics::WillLoadFrame(LocalFrame* frame, 
                                            const KURL& url, 
                                            int navigation_policy_enum,
                                            int request_context_enum,
                                            int frame_load_type_enum,
                                            Event* triggering_event,
                                            std::string event_type) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "load_url=" << url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "navigation_policy=" << navigation_policy_enum
          << _IFA_LOG_SPACE_ << "request_context=" << request_context_enum
          << _IFA_LOG_SPACE_ << "frame_load_type_enum=" << frame_load_type_enum
          << _IFA_LOG_SPACE_ << "triggering_event=" << triggering_event
          << _IFA_LOG_SPACE_ << "event_type=" << event_type.c_str()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::WillNavigateFrame(LocalFrame* frame, 
                                    LocalFrame* origin_frame,
                                    const KURL& url,
                                    bool replace_current_item) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_ 
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "origin_frame=" << origin_frame
          << _IFA_LOG_SPACE_ << "origin_frame_url=" 
              << origin_frame->GetDocument()->Url().GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "url=" << url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "replace_current_item=" << replace_current_item
          << _IFA_LOG_SPACE_ << "origin_frame_url=" 
              << origin_frame->GetDocument()->Url().GetString().Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::WillSendRequest(Document* document,
                            const KURL& url, int resource_type) {

  LocalFrame* frame = document->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_ 
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "url=" << url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "resource_type=" << resource_type
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidReceiveMainResourceRedirect(
                                            LocalFrame* frame, 
                                            const KURL& request_url,
                                            const KURL& redirect_url,
                                            int http_status_code) { 

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "request_url=" << request_url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "redirect_url=" << redirect_url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "http_status_code=" << http_status_code
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidHandleHttpRefresh(LocalFrame* frame, 
                                    const KURL& refresh_url, 
                                    Document::HttpRefreshType refresh_type) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "refresh_url=" << refresh_url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "refresh_type=" << refresh_type
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::RequestAnimationFrame(LocalFrame* frame, int id) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "callback_id=" << id
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::ExecuteFrameRequestCallbackBegin(ExecutionContext* context, int id) {

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "callback_id=" << id
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::ExecuteFrameRequestCallbackEnd(ExecutionContext* context, int id) {

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "callback_id=" << id
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::WillDownloadURL(LocalFrame* frame, 
          const KURL& url, const String& suggested_name) {

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "download_url=" << url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "suggested_name=" << suggested_name.Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


// Called when a script has been compiled
// and right before being executed
void Forensics::DidCompileScript(
        LocalFrame* frame, 
        const ScriptSourceCode& source,
        const int scriptID) {

  _IFA_DISABLE_

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << scriptID
          << " (" << source.StartPosition().line_.OneBasedInt() 
          << "," << source.StartPosition().column_.OneBasedInt() << ")"
          << _IFA_LOG_SPACE_ << "url=" << source.Url().GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "code=" << source.Source().Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

// Called when a compiled script has stopped running
// The time delta between DidCompileScript and DidRunCompiledScript
// should represent the actual script execution time,
// including nested script execution
void Forensics::DidRunCompiledScriptBegin(
        LocalFrame* frame, 
        const int scriptID,
        v8::Local<v8::Value> result) {

  _IFA_DISABLE_

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << scriptID
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidRunCompiledScriptEnd(
        LocalFrame* frame, 
        const int scriptID,
        v8::Local<v8::Value> result) {

  _IFA_DISABLE_

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << scriptID
          << _IFA_LOG_SPACE_ << "result=" 
              << V8ValueToString(GetChromeClient(frame), result)
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::DidCompileLazyEventListener(
                                 ExecutionContext* context, 
                                 const Node* node, 
                                 v8::Local<v8::Function> function, 
                                 const char* function_name, 
                                 const char* event_parameter_name, 
                                 const char* code, 
                                 const TextPosition& position, 
                                 const char* source_url) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  V8FunctionFeatures func_feat = 
            TranslateV8Function(GetChromeClient(frame), function);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
          << " (" << func_feat.line << "," << func_feat.column << ")"
          << _IFA_LOG_SPACE_ << "function_name=" << function_name
          << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name
          << _IFA_LOG_SPACE_ << "event_parameter_name=" << event_parameter_name
          << _IFA_LOG_SPACE_ << "code=" << code
          << _IFA_LOG_SPACE_ << "source_url=" << source_url
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());

}


// Should be called from
// ScriptModule::Compile
void Forensics::DidCompileModule(
        ExecutionContext* context, 
        const String& source,
        const KURL& source_url,
        const KURL& base_url,
        const TextPosition& text_position) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "source_url=" << source_url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "base_url=" << base_url.GetString().Utf8().data()
          << _IFA_LOG_SPACE_ << "source=" << source.Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());

}


// static
void Forensics::DidCallFunctionBegin(
        ExecutionContext* context,
        v8::Local<v8::Function> function,
        v8::Local<v8::Value> receiver,
        // FIXME(Roberto): remove argc
        // argc is not needed, if we pass args as vector
        const int argc,
        // FIXME(Roberto): pass as
        // v8::Local<v8::Value>* args
        // or at least by reference
        std::vector<v8::Local<v8::Value>> args) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  V8FunctionFeatures func_feat = 
            TranslateV8Function(GetChromeClient(frame), function);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
          << " (" << func_feat.line << "," << func_feat.column << ")"
          << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name;

  for(auto a : args) {
    log_str << _IFA_LOG_SPACE_ 
            << "arg_value=" << V8ValueToString(GetChromeClient(frame), a);
  }

  log_str << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidCallFunctionEnd(
        ExecutionContext* context,
        v8::Local<v8::Function> function,
        v8::Local<v8::Value> receiver,
        // FIXME(Roberto): remove argc
        // argc is not needed, if we pass args as vector
        const int argc,
        // FIXME(Roberto): pass as
        // v8::Local<v8::Value>* args
        // or at least by reference
        std::vector<v8::Local<v8::Value>> args) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  V8FunctionFeatures func_feat = 
            TranslateV8Function(GetChromeClient(frame), function);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
          << " (" << func_feat.line << "," << func_feat.column << ")"
          << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}
        

// Should be called from
// V8AbstractEventListener::handleEvent
void Forensics::DidCallHandleEventBegin(
          ExecutionContext* context,
          Event* event) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "event=" << event->type().Utf8().data()
          << _IFA_LOG_SPACE_ << "target=" << (void*)event->target()
          << _IFA_LOG_SPACE_ << "current_target=" << (void*)event->currentTarget()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidCallHandleEventEnd(
          ExecutionContext* context,
          Event* event) {

  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "event=" << event->type().Utf8().data()
          << _IFA_LOG_SPACE_ << "target=" << (void*)event->target()
          << _IFA_LOG_SPACE_ << "current_target=" << (void*)event->currentTarget()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


// Should be called from
// ScheduledAction::Execute(LocalFrame* frame)
void Forensics::DidFireScheduledActionBegin(
          ExecutionContext* context,
          v8::Local<v8::Function> function) {
  
  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  V8FunctionFeatures func_feat = 
            TranslateV8Function(GetChromeClient(frame), function);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
          << " (" << func_feat.line << "," << func_feat.column << ")"
          << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidFireScheduledActionEnd(
          ExecutionContext* context,
          v8::Local<v8::Function> function) {
  
  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  V8FunctionFeatures func_feat = 
            TranslateV8Function(GetChromeClient(frame), function);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
          << " (" << func_feat.line << "," << func_feat.column << ")"
          << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

// Should be called from
// ScheduledAction::Execute(LocalFrame* frame)
void Forensics::DidFireScheduledActionBegin(
          ExecutionContext* context,
          const String& code) {
  
  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "code=" << code.Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

void Forensics::DidFireScheduledActionEnd(
          ExecutionContext* context,
          const String& code) {
  
  _IFA_DISABLE_

  if(!context->ExecutingWindow())
    return;

  LocalFrame* frame = context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "code=" << code.Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


// static
void Forensics::DidCallV8SetAttribute(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, void* cpp_impl_ptr, 
            v8::Local<v8::Value> v8Value) {

  _IFA_DISABLE_

  if(!execution_context->ExecutingWindow())
    return;

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  string vStr = V8ValueToString(GetChromeClient(frame), v8Value);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SPACE_ << "cpp_class=" << cpp_class
          << _IFA_LOG_SPACE_ << "cpp_impl_ptr=" << cpp_impl_ptr
          << _IFA_LOG_SPACE_ << "value=" << vStr.c_str()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}

// static
void Forensics::DidCallV8SetAttributeEventListener(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, void* cpp_impl_ptr, 
            V8EventListener* listener, ScriptState* script_state) {

  _IFA_DISABLE_

  if(!execution_context->ExecutingWindow())
    return;

  if(!listener)
    return;

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  v8::Local<v8::Function> listener_function = 
              V8ListenerToV8Function(listener, script_state);

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SPACE_ << "cpp_class=" << cpp_class
          << _IFA_LOG_SPACE_ << "cpp_impl_ptr=" << cpp_impl_ptr;

  if(!listener_function.IsEmpty()) {
    V8FunctionFeatures func_feat = 
              TranslateV8Function(GetChromeClient(frame), listener_function);

    log_str << _IFA_LOG_SPACE_ << "scriptID=" << func_feat.scriptID
            << " (" << func_feat.line << "," << func_feat.column << ")"
            << _IFA_LOG_SPACE_ << "callback_debug_name=" << func_feat.debug_name
            << _IFA_LOG_SPACE_ << "code=" << listener->Code().Utf8().data();
  }
  else {
    log_str << _IFA_LOG_SPACE_ << "ERROR -- FAILED TO TRANSLATE V8EventListener";
  }

  log_str << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}





// static
void Forensics::DidCallV8MethodCallback(
            ExecutionContext* execution_context, 
            const char* interface, const char* attribute) {

  _IFA_DISABLE_

  if(!execution_context || !execution_context->ExecutingWindow()) {
    std::ostringstream log_str;
    log_str << _IFA_LOG_PREFIX_
            << _IFA_LOG_SPACE_ << "execution_context=" << execution_context
            << _IFA_LOG_SPACE_ << "interface=" << interface
            << _IFA_LOG_SPACE_ << "attribute=" << attribute
            << _IFA_LOG_SUFFIX_;
    LogInfo(log_str.str());
    
    return;
  }

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "execution_context=" << execution_context
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
} 

// static
void Forensics::DidCallV8Method(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, void* cpp_impl_ptr, 
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func) {

  DidCallV8MethodTemplate(execution_context, interface, attribute,
                          cpp_class, cpp_impl_ptr, args_list, args_func);

}

// static
void Forensics::DidCallV8Method(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, Node* cpp_impl_ptr, 
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func) {

  DidCallV8MethodTemplate(execution_context, interface, attribute,
                          cpp_class, cpp_impl_ptr, args_list, args_func);
}

// static
void Forensics::DidCallV8Method(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, EventTarget* cpp_impl_ptr, 
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func) {

  DidCallV8MethodTemplate(execution_context, interface, attribute,
                          cpp_class, cpp_impl_ptr, args_list, args_func);

}

// NOTE(Roberto): we could not directly use this as a probe:: because
// templates are not allowed by Chromium's build scripts
template <typename T>
void Forensics::DidCallV8MethodTemplate(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, T* cpp_impl_ptr, 
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func) {

  _IFA_DISABLE_

  if(!execution_context)
    return;

  if(!execution_context->ExecutingWindow())
    return;

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SPACE_ << "cpp_class=" << cpp_class
          << _IFA_LOG_SPACE_ << "cpp_impl_ptr=" << cpp_impl_ptr;

  for(auto a : args_list) {
    log_str << _IFA_LOG_SPACE_ << "arg_name=" << a.first
            << _IFA_LOG_SPACE_ << "arg_value=" 
                  << V8ValueToString(GetChromeClient(frame), a.second);
  }

  log_str << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::DidCallV8PostMessage(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            string& cpp_class, void* cpp_impl_ptr, 
            scoped_refptr<SerializedScriptValue> message) {

  _IFA_DISABLE_

  if(!execution_context)
    return;

  if(!execution_context->ExecutingWindow())
    return;

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SPACE_ << "cpp_class=" << cpp_class
          << _IFA_LOG_SPACE_ << "cpp_impl_ptr=" << cpp_impl_ptr
          << _IFA_LOG_SPACE_ << "message_length_bytes=" << (unsigned int) message->DataLengthInBytes()
          << _IFA_LOG_SPACE_ << "message=" << message->ToWireString().Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}


void Forensics::DidCallV8WindowPostMessage(
            ExecutionContext* execution_context, 
            string& interface, string& attribute, 
            LocalDOMWindow* src_window, DOMWindow* dst_window, 
            scoped_refptr<SerializedScriptValue> message) {

  _IFA_DISABLE_

  if(!execution_context)
    return;

  if(!execution_context->ExecutingWindow())
    return;

  LocalFrame* frame = execution_context->ExecutingWindow()->GetFrame();

  std::ostringstream log_str;
  log_str << _IFA_LOG_PREFIX_
          << _IFA_LOG_FRAME_
          << _IFA_LOG_SPACE_ << "interface=" << interface
          << _IFA_LOG_SPACE_ << "attribute=" << attribute
          << _IFA_LOG_SPACE_ << "src_window=" << src_window
          << _IFA_LOG_SPACE_ << "dst_window=" << dst_window
          << _IFA_LOG_SPACE_ << "message_length_bytes=" << (unsigned int) message->DataLengthInBytes()
          << _IFA_LOG_SPACE_ << "message=" << message->ToWireString().Utf8().data()
          << _IFA_LOG_SUFFIX_;
  LogInfo(log_str.str());
}



//-------------- PRIVATE ---------------//

// static
std::string Forensics::V8ValueToString(ChromeClient* client,
                                       v8::Local<v8::Value> v8Value) {

  std::string valueStr;

  if(!client)
    return valueStr;

  if(v8Value.IsEmpty())
    return valueStr;

  if(v8Value->IsNull()) {
    valueStr += "<=V8 VALUE NULL=>";
    return valueStr;
  }

  if(v8Value->IsNullOrUndefined()) {
    valueStr += "<=V8 VALUE UNDEFINED=>";
    return valueStr;
  }

  if(v8Value->IsFunction()) {
    V8FunctionFeatures ff = TranslateV8Function(client,
                                                v8Value.As<v8::Function>());
    valueStr += "<=V8 FUNCTION=> scriptID=";
    valueStr += std::to_string(ff.scriptID);
    valueStr += " (";
    valueStr += std::to_string(ff.line);
    valueStr += ",";
    valueStr += std::to_string(ff.column);
    valueStr += ") ";
    valueStr += ff.debug_name;
    return valueStr;
  }

  if(v8Value->IsObject()) {
    valueStr += "<=V8 OBJECT=>";
  }

  std::unique_ptr<base::Value> v = client->TranslateV8Value(v8Value);

  if(v == nullptr) {
    valueStr += "<=V8 VALUE UNKNOWN=>";
    return valueStr;
  }

  // valueStr += "==BASE_VALUE IS ";
  switch(v->type()) {
    case base::Value::Type::NONE : 
      // valueStr += "NONE!==";
      break;
    case base::Value::Type::BOOLEAN :
      // valueStr += "BOOLEAN!==";
      break;
    case base::Value::Type::INTEGER :
      // valueStr += "INTEGER!==";
      break;
    case base::Value::Type::DOUBLE  :
      // valueStr += "DOUBLE!==";
      break;
    case base::Value::Type::STRING  :
      // valueStr += "STRING!==";
      break;
    case base::Value::Type::BINARY  :
      // valueStr += "BINARY!==";
      break;
    case base::Value::Type::DICTIONARY :
      // valueStr += "DICTIONARY!==";
      break;
    case base::Value::Type::LIST    :
      // valueStr += "LIST!==";
      break;
    default :
      // valueStr += "UNKNOWN!==";
      break;
  }

  std::string jsonStr;
  JSONStringValueSerializer json(&jsonStr);

  valueStr += "::JSON::";
  if(json.Serialize(*v) && !jsonStr.empty()) {
    valueStr += jsonStr;
  }
  else {
    valueStr += "ERROR DURING JSON SERIALIZATION!";
  }
  valueStr += "::JSON::";

  return valueStr;

}

// static
Forensics::V8FunctionFeatures Forensics::TranslateV8Function(
                                            ChromeClient* client,
                                            v8::Local<v8::Function> func) {

    V8FunctionFeatures func_feat;

    if(!client)
      return func_feat;

    if(!func.IsEmpty()) {
      func_feat.scriptID = func->ScriptId();
      func_feat.line = func->GetScriptLineNumber()+1;
      func_feat.column = func->GetScriptColumnNumber()+1;

      std::unique_ptr<base::Value> v = 
                client->TranslateV8Value(func->GetDebugName());

      if(v != nullptr && v->type() == base::Value::Type::STRING)
        func_feat.debug_name = v->GetString();
    }

    return func_feat;
}


// static
v8::Local<v8::Function> Forensics::V8ListenerToV8Function(
                                        V8EventListener* listener,
                                        ScriptState* script_state) {

  ForensicsV8EventListener* l_ptr = 
              static_cast<ForensicsV8EventListener*>(listener);

  if(!l_ptr) 
    return v8::Local<v8::Function>();

  return l_ptr->GetListenerFunction(script_state);
}


} // namespace blink

