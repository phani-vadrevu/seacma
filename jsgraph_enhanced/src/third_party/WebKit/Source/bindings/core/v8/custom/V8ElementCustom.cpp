// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "bindings/core/v8/V8Element.h"

#include "bindings/core/v8/ExceptionState.h"
#include "bindings/core/v8/IDLTypes.h"
#include "bindings/core/v8/V8TrustedHTML.h"
#include "core/html/custom/V0CustomElementProcessingStack.h"

// :: Forensics ::
#include "core/inspector/Forensics.h"
#include "bindings/core/v8/V8BindingForCore.h"
// 

namespace blink {

// HTMLElement -----------------------------------------------------------------

void V8Element::innerHTMLAttributeSetterCustom(
    v8::Local<v8::Value> value,
    const v8::FunctionCallbackInfo<v8::Value>& info) {
  v8::Isolate* isolate = info.GetIsolate();

  v8::Local<v8::Object> holder = info.Holder();

  Element* impl = V8Element::ToImpl(holder);

  V0CustomElementProcessingStack::CallbackDeliveryScope delivery_scope;

  ExceptionState exception_state(isolate, ExceptionState::kSetterContext,
                                 "Element", "innerHTML");

  // Prepare the value to be set.
  StringOrTrustedHTML cpp_value;
  // This if statement is the only difference to the generated code and ensures
  // that only null but not undefined is treated as the empty string.
  // https://crbug.com/783916
  if (value->IsNull()) {
    cpp_value.SetString(String());
  } else {
    V8StringOrTrustedHTML::ToImpl(info.GetIsolate(), value, cpp_value,
                                  UnionTypeConversionMode::kNotNullable,
                                  exception_state);
  }
  if (exception_state.HadException())
    return;

  // :: Forensics ::
  ExecutionContext* execution_context_F = CurrentExecutionContext(info.GetIsolate());
  std::string interface_name_F = "Element";
  std::string attribute_name_F = "innerHTML";
  std::string cpp_class_name_F = "Element";
  void* cpp_class_ptr_F = impl;

  Forensics::DidCallV8SetAttribute(execution_context_F, 
                               interface_name_F,
                               attribute_name_F,
                               cpp_class_name_F,
                               cpp_class_ptr_F,
                               value);
  //

  impl->setInnerHTML(cpp_value, exception_state);
}

void V8Element::outerHTMLAttributeSetterCustom(
    v8::Local<v8::Value> value,
    const v8::FunctionCallbackInfo<v8::Value>& info) {
  v8::Isolate* isolate = info.GetIsolate();

  v8::Local<v8::Object> holder = info.Holder();

  Element* impl = V8Element::ToImpl(holder);

  V0CustomElementProcessingStack::CallbackDeliveryScope delivery_scope;

  ExceptionState exception_state(isolate, ExceptionState::kSetterContext,
                                 "Element", "outerHTML");

  // Prepare the value to be set.
  StringOrTrustedHTML cpp_value;
  // This if statement is the only difference to the generated code and ensures
  // that only null but not undefined is treated as the empty string.
  // https://crbug.com/783916
  if (value->IsNull()) {
    cpp_value.SetString(String());
  } else {
    V8StringOrTrustedHTML::ToImpl(info.GetIsolate(), value, cpp_value,
                                  UnionTypeConversionMode::kNotNullable,
                                  exception_state);
  }
  if (exception_state.HadException())
    return;

  // :: Forensics ::
  ExecutionContext* execution_context_F = CurrentExecutionContext(info.GetIsolate());
  std::string interface_name_F = "Element";
  std::string attribute_name_F = "outerHTML";
  std::string cpp_class_name_F = "Element";
  void* cpp_class_ptr_F = impl;

  Forensics::DidCallV8SetAttribute(execution_context_F, 
                               interface_name_F,
                               attribute_name_F,
                               cpp_class_name_F,
                               cpp_class_ptr_F,
                               value);
  //

  impl->setOuterHTML(cpp_value, exception_state);
}

}  // namespace blink
