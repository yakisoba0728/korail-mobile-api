# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""Generated from the reviewed 7.0.6 Retrofit inventory. Do not edit."""

CONTRACT_ROWS = (
    {'interface': 'NetworkApi',
     'method': 'executeOnlineRefunds',
     'http': 'POST',
     'route': '/classes/com.korail.mobile.refunds.executeOnlineRefunds',
     'params': 'FieldMap',
     'form': True,
     'request_model': 'ExecuteOnlineRefundsIn',
     'response_model': 'com.korail.talk.network.model.ExecuteOnlineRefundsOut',
     'effect': 'mutation'},
    {'interface': 'NetworkApi',
     'method': 'verifyOnlineRefunds',
     'http': 'POST',
     'route': '/classes/com.korail.mobile.refunds.verifyOnlineRefunds',
     'params': 'FieldMap',
     'form': True,
     'request_model': 'VerifyOnlineRefundsIn',
     'response_model': 'com.korail.talk.network.model.VerifyOnlineRefundsOut',
     'effect': 'read'},
)
