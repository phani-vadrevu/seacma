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
// Copyright 2018 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef TimeClamper_h
#define TimeClamper_h

#include "base/macros.h"
#include "platform/PlatformExport.h"

#include <stdint.h>

namespace blink {

class PLATFORM_EXPORT TimeClamper {
 public:
  // :: Forensics ::
  //static constexpr double kResolutionSeconds = 0.0001;
  static constexpr double kResolutionSeconds = 0.1;
  //

  TimeClamper();

  // Deterministically clamp the time value |time_seconds| to a 100us interval
  // to prevent timing attacks. See
  // http://www.w3.org/TR/hr-time-2/#privacy-security.
  //
  // For each clamped time interval, we compute a pseudorandom transition
  // threshold. The returned time will either be the start of that interval or
  // the next one depending on which side of the threshold |time_seconds| is.
  double ClampTimeResolution(double time_seconds) const;

 private:
  inline double ThresholdFor(double clamped_time) const;
  static inline double ToDouble(uint64_t value);
  static inline uint64_t MurmurHash3(uint64_t value);

  uint64_t secret_;

  DISALLOW_COPY_AND_ASSIGN(TimeClamper);
};

}  // namespace blink

#endif  // TimeClamper_h
