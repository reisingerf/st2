# -*- coding: utf-8 -*-
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
import six
import logging
from oslo_config import cfg
from st2common.services.keyvalues import get_kvp_for_name
from st2common.persistence.keyvalue import KeyValuePair
from st2common.exceptions.db import StackStormDBObjectNotFoundError
from st2common.util.crypto import symmetric_decrypt
from st2common.models.api.keyvalue import KeyValuePairAPI
from st2common.services.config import deserialize_key_value
from st2common.constants.keyvalue import (ALL_SCOPE, FULL_SYSTEM_SCOPE,
                                          FULL_USER_SCOPE, USER_SCOPE,
                                          ALLOWED_SCOPES)
from st2common.services.keyvalues import get_key_reference
from st2common.rbac import utils as rbac_utils
from st2common.util.keyvalue import get_datastore_full_scope
from st2common.models.db.auth import UserDB

LOG = logging.getLogger(__name__)

def _to_dict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.iteritems() 
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def _validate_scope(scope):
    if scope not in ALLOWED_SCOPES:
        msg = 'Scope %s is not in allowed scopes list: %s.' % (scope, ALLOWED_SCOPES)
        raise ValueError(msg)


def _validate_decrypt_query_parameter(decrypt, scope, is_admin, user):
    """
    Validate that the provider user is either admin or requesting to decrypt value for
    themselves.
    """
    is_user_scope = (scope == USER_SCOPE or scope == FULL_USER_SCOPE)
    if decrypt and (not is_user_scope and not is_admin):
        msg = 'Decrypt option requires administrator access'
        raise AccessDeniedError(message=msg, user_db=user)


def st2kv_(context, key, decrypt=False):
    if not isinstance(key, six.string_types):
        raise TypeError('Given key is not typeof string.')
    if not isinstance(decrypt, bool):
        raise TypeError('Decrypt parameter is not typeof bool.')

    if key.startswith('system.'):
        scope = FULL_SYSTEM_SCOPE
        key_id = key[key.index('.') + 1:]
    else:
        scope = FULL_USER_SCOPE
        key_id = key

    LOG.debug('Context: %s', _to_dict(context))

    user = 'testu'

    if not user:
        user = UserDB(cfg.CONF.system_user.user)

    scope = get_datastore_full_scope(scope)

    _validate_scope(scope=scope)

    is_admin = rbac_utils.user_is_admin(user_db=user)

    # User needs to be either admin or requesting item for itself
    _validate_decrypt_query_parameter(decrypt=decrypt, scope=scope, is_admin=is_admin,
                                      user=user)

    key_ref = get_key_reference(scope=scope, name=key_id, user=user)

    value = KeyValuePair.get_by_scope_and_name(scope, key_id)

    LOG.debug('Decrypt: %s', decrypt)
    LOG.debug('Scope: %s', scope)
    LOG.debug('Admin: %s', is_admin)
    LOG.debug('Key: %s', key_id)
    LOG.debug('Bleh: %s', value)

    if value:
        return deserialize_key_value(
            value.value,
            decrypt
        )

    return None
