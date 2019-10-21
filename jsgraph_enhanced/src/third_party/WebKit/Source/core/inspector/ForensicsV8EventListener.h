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
#ifndef ForensicsV8EventListener_h
#define ForensicsV8EventListener_h

#include "core/inspector/Forensics.h"
#include "bindings/core/v8/V8EventListener.h"

namespace blink {

class ForensicsV8EventListener : public V8EventListener {
  friend class Forensics;
};

}

#endif // ForensicsV8EventListener_h
