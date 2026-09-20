# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

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
