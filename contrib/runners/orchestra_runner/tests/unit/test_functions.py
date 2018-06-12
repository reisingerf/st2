# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

import unittest2

from functions.st2kv import st2kv_
from st2common.exceptions.db import StackStormDBObjectNotFoundError


class TestST2KV(unittest2.TestCase):
    @mock.patch('functions.st2kv.get_kvp_for_name')
    def test_valid_return(self, get_kvp_patch):
        key = 'test'
        get_kvp_patch.return_value = key

        result = st2kv_(None, key)

        self.assertEquals(key, result)

    @mock.patch('functions.st2kv.get_kvp_for_name')
    def test_not_found_return(self, get_kvp_patch):
        get_kvp_patch.side_effect = StackStormDBObjectNotFoundError('Not Found')

        result = st2kv_(None, 'test')

        self.assertEquals(None, result)

    def test_invalid_input(self):
        self.assertRaises(TypeError, st2kv_, None, 123)
        self.assertRaises(TypeError, st2kv_, None, dict())
        self.assertRaises(TypeError, st2kv_, None, object())
        self.assertRaises(TypeError, st2kv_, None, [1, 2])
