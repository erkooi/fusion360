################################################################################
# Copyright 2023 E. Kooistra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
# Author: Eric Kooistra.
# Date: 17 Mar 2023
"""Append local API/libraries dir for Fusion 360 to sys.path.

Use copy of this script in API/Script or API/AddIn directory to append path to
local libraries to sys.path. This avoids having to use this append code in the
API script and allows to put the local libraries in a parent dir. Ignore
Fusion 360 recommendion to not append to sys.path.
"""

import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
utilitiesdir = os.path.dirname(currentdir)
apidir = os.path.dirname(utilitiesdir)
librariesdir = os.path.join(apidir, 'libraries')
if librariesdir not in sys.path:
    sys.path.append(librariesdir)
