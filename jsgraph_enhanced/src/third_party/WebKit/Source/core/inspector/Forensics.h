/////////////////////////////////////////////////////////////////////////////
// Copyright (C) 2018 Roberto Perdisci                                     //
// perdisci@cs.uga.edu                                                     //
//                                                                         //
// Distributed under the GNU Public License                                //
// http://www.gnu.org/licenses/gpl.txt                                     //
//                                                                         //
// This program is free software; you can redistribute it and/or modify    //
// it under the terms of the GNU General Public License as published by    //
// the Free Software Foundation; either version 2 of the License, or       //
// (at your option) any later version.                                     //
//                                                                         //
/////////////////////////////////////////////////////////////////////////////
#ifndef Forensics_h
#define Forensics_h

#include "core/CoreExport.h"
#include "v8/include/v8.h"
#include "platform/wtf/text/TextPosition.h"
#include "core/loader/FrameLoaderTypes.h"
#include "core/dom/Document.h"

namespace blink {

class Frame;
class ChromeClient;
class Node;
class ExecutionContext;
class WebThread;
class V8EventListener;
class ScriptSourceCode;
class ScriptState;
class EventTarget;
class SerializedScriptValue;
class DOMWindow;
class LocalDOMWindow;
class Event;
class KURL;

struct WebWindowFeatures;

using ArgNameValPair = std::pair<std::string,v8::Local<v8::Value>>;
using ArgNameListenerPair = std::pair<std::string,V8EventListener*>;

class CORE_EXPORT Forensics final {
  WTF_MAKE_NONCOPYABLE(Forensics);

 public:

  static void LogInfo(std::string log_str);
  

  // Methods called from the InspectorInstrumentation.
  static bool IsWhitespace(Node*);
  static void DidInsertDOMNode(Node*);
  static void WillRemoveDOMNode(Node*);

  // Methods called when navigating

  static
  void WindowCreated(LocalFrame* created);

  static
  void WindowOpen(Document* document,
                  const String& url,
                  const AtomicString& window_name,
                  const WebWindowFeatures& window_features,
                  bool user_gesture);

  static
  void DidCreateDocumentLoader(LocalFrame* frame, 
                               const KURL& url, 
                               FrameLoadType load_type, 
                               NavigationType navigation_type);
  
  static
  void WillLoadFrame(LocalFrame* frame,
                     const KURL& url, 
                     int navigation_policy_enum,
                     int request_context_enum,
                     int frame_load_type_enum,
                     Event* triggering_event,
                     std::string event_type);

  static
  void WillNavigateFrame(LocalFrame* frame, 
                         LocalFrame* origin_frame,
                         const KURL& url,
                         bool replace_current_item);

  static
  void WillSendRequest(Document* document, const KURL& url, int resource_type);

  static
  void DidCreateChildFrame(LocalFrame* frame,
                           LocalFrame* child_frame,
                           const char* child_name,
                           Node* owner_element);

  static
  void DidReceiveMainResourceRedirect(LocalFrame* frame, 
                                      const KURL& request_url,
                                      const KURL& redirect_url, 
                                      int http_status_code);

  static
  void DidHandleHttpRefresh(LocalFrame* frame, 
                            const KURL& refresh_url, 
                            Document::HttpRefreshType refresh_type);

  static
  void RequestAnimationFrame(LocalFrame* frame, int id);

  static
  void ExecuteFrameRequestCallbackBegin(ExecutionContext* context, int id);

  static
  void ExecuteFrameRequestCallbackEnd(ExecutionContext* context, int id);

  static
  void LoadEventFired(LocalFrame* frame);

  static
  void WillDownloadURL(LocalFrame* frame, 
                       const KURL& url, 
                       const String& suggested_name);


  // Methods called when compiling or executing JS code

  static
  void DidCompileScript(LocalFrame* frame, 
            const ScriptSourceCode& source, const int scriptID);

  static
  void DidCompileLazyEventListener(ExecutionContext* context, 
                                   const Node* node, 
                                   v8::Local<v8::Function> function, 
                                   const char* function_name, 
                                   const char* event_parameter_name, 
                                   const char* code, 
                                   const TextPosition& position, 
                                   const char* source_url);

  static
  void DidCompileModule(ExecutionContext* context, const String& source, 
            const KURL& source_url, const KURL& base_url,
            const TextPosition& text_position);

  static
  void DidRunCompiledScriptBegin(LocalFrame* frame, 
            const int scriptID, v8::Local<v8::Value> result);

  static
  void DidRunCompiledScriptEnd(LocalFrame* frame, 
            const int scriptID, v8::Local<v8::Value> result);

  static
  void DidCallFunctionBegin(ExecutionContext* context,
            v8::Local<v8::Function> function,
            v8::Local<v8::Value> receiver,
            const int argc, std::vector<v8::Local<v8::Value>> args);

  static
  void DidCallFunctionEnd(ExecutionContext* context,
            v8::Local<v8::Function> function,
            v8::Local<v8::Value> receiver,
            const int argc, std::vector<v8::Local<v8::Value>> args);

  static
  void DidCallHandleEventBegin(ExecutionContext* context, Event* event);

  static
  void DidCallHandleEventEnd(ExecutionContext* context, Event* event);

  static
  void DidFireScheduledActionBegin(ExecutionContext* context,
            v8::Local<v8::Function> function);

  static
  void DidFireScheduledActionEnd(ExecutionContext* context,
            v8::Local<v8::Function> function);

  static
  void DidFireScheduledActionBegin(ExecutionContext* context, 
            const String& code);

  static
  void DidFireScheduledActionEnd(ExecutionContext* context, 
            const String& code);



  // Methods called from the Bindings instrumentation.

  static
  void DidCallV8SetAttribute(
            ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute, 
            std::string& cpp_class, void* cpp_impl_ptr, 
            v8::Local<v8::Value> v8Value); 

  static
  void DidCallV8SetAttributeEventListener(
            ExecutionContext* execution_context,
            std::string& interface, std::string& attribute,
            std::string& cpp_class, void* cpp_impl_ptr,
            V8EventListener* listener, ScriptState* script_state); 

  static
  void DidCallV8MethodCallback(ExecutionContext* execution_context, 
            const char* interface, const char* attribute);

  static
  void DidCallV8Method(ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute,
            std::string& cpp_class, void* cpp_impl_ptr,
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func);

  static
  void DidCallV8Method(ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute,
            std::string& cpp_class, Node* cpp_impl_ptr,
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func);

  static
  void DidCallV8Method(ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute,
            std::string& cpp_class, EventTarget* cpp_impl_ptr,
            std::vector<ArgNameValPair> args_list,
            std::vector<ArgNameListenerPair> args_func);

  static
  void DidCallV8PostMessage(ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute, 
            std::string& cpp_class, void* cpp_impl_ptr, 
            scoped_refptr<SerializedScriptValue> message);

  static
  void DidCallV8WindowPostMessage(ExecutionContext* execution_context, 
            std::string& interface, std::string& attribute, 
            LocalDOMWindow* src_window, DOMWindow* dst_window,
            scoped_refptr<SerializedScriptValue> message);

 private:

  struct V8FunctionFeatures {
    int scriptID = 0;
    int line = 0;
    int column = 0; 
    std::string debug_name;
  };

  static std::string V8ValueToString(ChromeClient* client,
                                     v8::Local<v8::Value> v8Value);

  static V8FunctionFeatures TranslateV8Function(
                                     ChromeClient* client,
                                     v8::Local<v8::Function> func);

  static v8::Local<v8::Function> V8ListenerToV8Function(
                                     V8EventListener* listener, 
                                     ScriptState* script_state);

  template <typename T>
  static void DidCallV8MethodTemplate(ExecutionContext* execution_context, 
                    std::string& interface, std::string& attribute,
                    std::string& cpp_class, T* cpp_impl_ptr,
                    std::vector<ArgNameValPair> args_list,
                    std::vector<ArgNameListenerPair> args_func);

  static Document* GetDocument(LocalFrame* frame);
  static String GetDocumentURL(LocalFrame* frame);
  static LocalFrame* GetFrameRoot(LocalFrame* frame);
  static String GetFrameRootURL(LocalFrame* frame);
  static Frame* GetMainFrame(LocalFrame* frame);
  static ChromeClient* GetChromeClient(LocalFrame* frame);

  
};

} // namespace blink

#endif // !defined(Forensics_h)
