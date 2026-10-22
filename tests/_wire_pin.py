"""Captured by test_wire_equivalence.py at tag pre-3.0-overhaul (4412c93). Do not regenerate."""

import json

WIRE_PIN = json.loads(r"""{
 "login": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "logout": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Logout",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  }
 ],
 "clear_session": [],
 "close": [],
 "search_trains": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "search_transfer_trains": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "2"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "search_trains_with_transfer_fallback": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_transfer_stations": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.qry.chtnStn.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ]
   ]
  }
 ],
 "get_train_calendar": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.schedule.runDt",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  }
 ],
 "get_seat_cars": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.TrainResearch",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtRunDt",
     "20990102"
    ],
    [
     "txtDptDt",
     "20990102"
    ],
    [
     "txtTrnNo",
     "90001"
    ],
    [
     "txtDptTm",
     "090000"
    ],
    [
     "txtTrnClsfCd",
     "00"
    ],
    [
     "txtTrnGpCd",
     "100"
    ],
    [
     "txtDptRsStnCd",
     "9901"
    ],
    [
     "txtArvRsStnCd",
     "9903"
    ],
    [
     "txtPsrmClCd",
     "1"
    ],
    [
     "txtSeatAttCd",
     "015"
    ],
    [
     "txtDptStnRunOrdr",
     "1"
    ],
    [
     "txtArvStnRunOrdr",
     "3"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ]
   ]
  }
 ],
 "get_seat_inventory": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.TResidualSeatsResearch.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "trnClsfCd",
     "00"
    ],
    [
     "trnGpCd",
     "100"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "srcarNo",
     "1"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "dptStnRunOrdr",
     "1"
    ],
    [
     "arvStnRunOrdr",
     "3"
    ],
    [
     "totPsgCnt",
     "1"
    ],
    [
     "isArrow",
     "false"
    ]
   ]
  }
 ],
 "get_free_seat_car_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.trn.fresScar.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "dptStnConsOrdr",
     "1"
    ],
    [
     "arvStnConsOrdr",
     "3"
    ],
    [
     "dptStnRunOrdr",
     "1"
    ],
    [
     "arvStnRunOrdr",
     "3"
    ]
   ]
  }
 ],
 "get_guide_seat_condition": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservation.guideSeatCnd.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "rqSeatAttCd",
     "015"
    ]
   ]
  }
 ],
 "get_merge_seats_inquiry": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.mergeSeatsC.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "abrdDt",
     "20990102090000"
    ],
    [
     "runDt",
     "20990102090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "dptRsStnNm",
     "출발시험역"
    ],
    [
     "arvRsStnNm",
     "도착시험역"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "totPsgNum",
     "1"
    ]
   ]
  }
 ],
 "get_price_fare_quote": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.trn.prcFare.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "chtnDvCd",
     "1"
    ],
    [
     "trnCnt",
     "1"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "gdNo",
     ""
    ],
    [
     "rqSeatAttCd",
     "015"
    ],
    [
     "trnGpCd",
     "100"
    ],
    [
     "stlbTrnClsfCd",
     "00"
    ]
   ]
  }
 ],
 "get_station_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.stationinfo",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_station_data": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.stationdata",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_common_code": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "code",
     "synthetic.code"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  }
 ],
 "get_app_data": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_notice": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_uuid": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/ebizcross/getUUID.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_service_status": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "timeStamp",
     "1"
    ]
   ]
  }
 ],
 "get_maas_menu_list": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.copt.gdMenuLt.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  }
 ],
 "get_maas_station_data": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/ebizmaas/EbizMaasStationList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "addSrvDvCd",
     "SYNTHETIC-SERVICE"
    ]
   ]
  }
 ],
 "get_maas_service_details": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.copt.gdReqQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "qryDtFrom",
     "20990102"
    ],
    [
     "qryDtTo",
     "20990102"
    ]
   ]
  }
 ],
 "get_cart_list": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.cart.showCartList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "pnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "get_deposit_banks": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "AppVersion",
     "7.0.8"
    ]
   ]
  }
 ],
 "get_delay_discount_tickets": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.passCard.DelayDiscountView",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_page_no",
     "20990102"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_discount_coupons": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.passCard.CouponView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtSelPage",
     "1"
    ],
    [
     "pnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "get_korail_point_summary": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.xPoint.MyXPointView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "point_dv_cd",
     "0"
    ]
   ]
  }
 ],
 "get_mileage_history": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.mlg.amtSpec.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "pontTpVal",
     "1"
    ],
    [
     "qryDvVal",
     "0"
    ],
    [
     "qryStDt",
     "20990102"
    ],
    [
     "qryClsDt",
     "20990102"
    ],
    [
     "pgPrCnt",
     "20"
    ],
    [
     "nowPgNo",
     "1"
    ]
   ]
  }
 ],
 "get_discount_card_usage_history": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.ticket.dcntCrdUseQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dcntCrdNo",
     "SYNTHETIC-CARD"
    ]
   ]
  }
 ],
 "get_discount_card_schedule": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.dcntCrdScheduleView.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnNm",
     "출발시험역"
    ],
    [
     "arvRsStnNm",
     "도착시험역"
    ],
    [
     "dptTm",
     "000000"
    ],
    [
     "trnGpCd",
     "109"
    ],
    [
     "dirtChtnDvCd",
     "1"
    ],
    [
     "dcntCrdKndCd",
     "MMM"
    ],
    [
     "dcntCrdKndMgNo",
     "SYNTHETIC-KIND"
    ]
   ]
  }
 ],
 "get_pass_available_dates": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.pass.passInfoList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtCmtrKndCd",
     "SYNTHETIC-KIND"
    ],
    [
     "txtCmtrUtlTrmCd",
     "1"
    ],
    [
     "txtCmtrUtlAgeCd",
     "1"
    ]
   ]
  }
 ],
 "get_pass_schedule": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.pass.passScheduleInfoList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "selGoTrain",
     "100"
    ],
    [
     "selGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "radChgTrnDvCd",
     "1"
    ],
    [
     "txtCmtrKndCd",
     "SYNTHETIC-KIND"
    ],
    [
     "txtCmtrUtlTrmCd",
     "1"
    ],
    [
     "txtCmtrUtlAgeCd",
     "1"
    ],
    [
     "txtSelPage",
     "1"
    ],
    [
     "txtCntPerPage",
     "10"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtWkndUseFlg",
     "N"
    ]
   ]
  }
 ],
 "get_trip_menu": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.pass.trGdMenuLt.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  }
 ],
 "get_pass_menu": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.pass.passMenu.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "menuNo",
     "SYNTHETIC-MENU"
    ]
   ]
  }
 ],
 "get_crew_request_list": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.crwCallRq.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_commuter_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.cmtrInfo.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "jobDvCd",
     "c"
    ],
    [
     "psgCnt",
     "0"
    ],
    [
     "ogtkSaleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "ogtkSaleDd",
     "20990102"
    ],
    [
     "ogtkSaleSqno",
     "1"
    ],
    [
     "ogtkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "inquiryType",
     "0"
    ]
   ]
  }
 ],
 "get_product_reservations": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.product.ReservationList",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtSelPage",
     "1"
    ],
    [
     "txtCntPerPage",
     "10"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_product_detail": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.product.ReservationDetail",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtVrRsNo",
     "SYNTHETIC-RESERVATION"
    ],
    [
     "txtVrRsvSqNo",
     "1"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_ticket_receipt": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.receipt.ReceiptInfo",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_sale_dt",
     "0102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_tk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "get_reservation_history": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_21"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservation.ReservationView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "0"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_seat_assignment_schedule": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.assignScheduleView.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "menuId",
     "11"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "dptRsStnNm",
     "출발시험역"
    ],
    [
     "arvRsStnNm",
     "도착시험역"
    ],
    [
     "trnGpCd",
     "100"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dirtChtnDvCd",
     "1"
    ],
    [
     "seatAttCd1",
     "015"
    ],
    [
     "psgNum1",
     "1"
    ],
    [
     "stlbDturDvNm1",
     "N"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_multi_child_discount_targets": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.cust.mchdDcntTgt.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ]
   ]
  }
 ],
 "get_customer_trip_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.custTripInfo.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "custMgNo",
     "SYNTHETIC-CUSTOMER"
    ],
    [
     "medDvCd",
     "03"
    ],
    [
     "regSqno",
     "0"
    ]
   ]
  }
 ],
 "get_trip_change_dates": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservation.tripChgDate.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "tripChgDate",
     "20990102"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_delivery_recipient": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.tk.dlvRcvCust.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDt",
     "20990102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "check_ticket_duplication": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.ticket.ticketDupCheck.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "pnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "get_pbp_acceptance_specifications": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.tk.pbpAcepSpec.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "tkCnt",
     "1"
    ],
    [
     "tkRetNo",
     "SYNTHETIC-WINDOW-20990102-1-SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "get_original_ticket_inquiry": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.tripChgOgtk.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "tkCnt",
     "1"
    ],
    [
     "ogtkSaleWctNo_1",
     "SYNTHETIC-WINDOW"
    ],
    [
     "ogtkSaleDd_1",
     "20990102"
    ],
    [
     "ogtkSaleSqno_1",
     "1"
    ],
    [
     "ogtkRetPwd_1",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "get_self_seat_change_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.self.seatChgInfo.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ]
   ]
  }
 ],
 "get_recent_delivery_history": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.tk.rcntDlvHst.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "custMgNo",
     "SYNTHETIC-CUSTOMER"
    ]
   ]
  }
 ],
 "get_ticket_reservation_detail": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.ReservationList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "get_refund_commission": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "get_refund_ticket_detail": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.SelTicketInfo",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "h_purchase_history",
     "N"
    ]
   ]
  }
 ],
 "get_ticket_list": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "reserve": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "reserve_transfer": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtSeatAttCd4_1",
     "015"
    ],
    [
     "txtJrnyCnt",
     "2"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "14"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9902"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "2"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ],
    [
     "txtJrnyTpCd2",
     "14"
    ],
    [
     "txtJrnySqno2",
     "002"
    ],
    [
     "txtTrnNo2",
     "90002"
    ],
    [
     "txtTrnClsfCd2",
     "00"
    ],
    [
     "txtTrnGpCd2",
     "100"
    ],
    [
     "txtRunDt2",
     "20990102"
    ],
    [
     "txtDptDt2",
     "20990102"
    ],
    [
     "txtDptTm2",
     "101000"
    ],
    [
     "txtDptRsStnCd2",
     "9902"
    ],
    [
     "txtDptStnConsOrdr2",
     "1"
    ],
    [
     "txtDptStnRunOrdr2",
     "2"
    ],
    [
     "txtArvRsStnCd2",
     "9903"
    ],
    [
     "txtArvStnConsOrdr2",
     "3"
    ],
    [
     "txtArvStnRunOrdr2",
     "3"
    ],
    [
     "txtChgFlg2",
     "N"
    ],
    [
     "txtPsrmClCd2",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "reserve_merge": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1202"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "Y"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ],
    [
     "txtMidRsStnCd",
     "9902"
    ],
    [
     "txtMidStnConsOrdr",
     "2"
    ],
    [
     "txtMidStnRunOrdr",
     "2"
    ]
   ]
  }
 ],
 "reserve_with_discount_card": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "A2"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "153"
    ],
    [
     "txtCardNo_1",
     "SYNTHETIC-CARD"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "confirm_standby_hold": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservationWait.ReservationWait",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "txtPsrmClChgFlg",
     "N"
    ],
    [
     "txtSmsSndFlg",
     "N"
    ]
   ]
  }
 ],
 "cancel_unpaid_hold": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservationCancel.ReservationCancel",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "txtJrnySqno",
     "0001"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "hidRsvChgNo",
     "000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "txtJrnySqno",
     "0001"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "hidRsvChgNo",
     "000"
    ]
   ]
  }
 ],
 "cancel_product_reservation": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.product.ReservationCancel",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtVrRsNo",
     "SYNTHETIC-RESERVATION"
    ],
    [
     "txtGdSqno",
     "1"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "pay_with_card": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "refund": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.RefundsRequest",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "h_orgtk_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_sale_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "h_mlg_stl",
     "N"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "verify_station_ticket_refund": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.verifyOnlineRefunds",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "strName",
     "SYNTHETIC-NAME"
    ],
    [
     "retNo1",
     "00000"
    ],
    [
     "retNo2",
     "00000000"
    ],
    [
     "retNo3",
     "0000000"
    ],
    [
     "retNo4",
     "00000"
    ]
   ]
  }
 ],
 "execute_station_ticket_refund": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.executeOnlineRefunds",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "pnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "ogtkSaleDt",
     "20990102"
    ],
    [
     "ogtkSaleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "ogtkSaleSqno",
     "1"
    ],
    [
     "ogtkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "retDvCd",
     "1"
    ],
    [
     "retRsnCd",
     "1"
    ],
    [
     "tkKndCd",
     "1"
    ],
    [
     "custTeln",
     "00000000000"
    ],
    [
     "retAmt",
     "1000"
    ],
    [
     "retFee",
     "0"
    ],
    [
     "acepCustNm",
     "SYNTHETIC-NAME"
    ]
   ]
  }
 ],
 "add_to_cart": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.cart.addCartList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "register_discount_card": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.dcntCrdInfo.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dcntCrdKndMgNo",
     "SYNTHETIC-KIND"
    ],
    [
     "custMgNo",
     "SYNTHETIC-CUSTOMER"
    ],
    [
     "vlidTrmStDt",
     "20990102"
    ],
    [
     "usePsbTno",
     "1"
    ],
    [
     "jrnyCnt",
     "1"
    ],
    [
     "jrnyTpCd_1",
     "11"
    ],
    [
     "runDt_1",
     "20990102"
    ],
    [
     "trnNo_1",
     "90001"
    ],
    [
     "dptRsStnCd_1",
     "9901"
    ],
    [
     "arvRsStnCd_1",
     "9903"
    ]
   ]
  }
 ],
 "extend_discount_card": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.reservation.dcntCrdExtn.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDd",
     "20990102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "recalculate_price": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.PriceReCalculation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "txtPsgGridcnt",
     "1"
    ],
    [
     "psg_tp_dv_cd",
     "1"
    ],
    [
     "psrm_cl_cd",
     "1"
    ],
    [
     "dcnt_knd_cd1",
     "000"
    ],
    [
     "hidDscpNo",
     ""
    ],
    [
     "hidDcntKndCd",
     ""
    ],
    [
     "hidFmlyNo",
     ""
    ]
   ]
  }
 ],
 "get_limousine_schedules": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ],
 "get_limousine_seat_inventory": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lms.TResidualSeatsResearch.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "trnClsfCd",
     "80"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "srcarNo",
     "0001"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "dptStnRunOrdr",
     "1"
    ],
    [
     "arvStnRunOrdr",
     "3"
    ],
    [
     "totPsgCnt",
     "1"
    ],
    [
     "isArrow",
     "false"
    ]
   ]
  }
 ],
 "reserve_limousine": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtSrcarCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "80"
    ],
    [
     "txtTrnGpCd1",
     "800"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ],
    [
     "txtSrcarNo1",
     "0001"
    ],
    [
     "txtSeatNo1",
     "1A"
    ]
   ]
  }
 ],
 "get_delay_certificate": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.athnIsu.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "ogtkSaleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "ogtkSaleDd",
     "20990102"
    ],
    [
     "ogtkSaleSqno",
     "1"
    ],
    [
     "ogtkRetPwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "get_delay_return_receipt": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.pymtRcet.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDd",
     "20990102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "retrieve_delivered_ticket": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.tk.pbpWdrw.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "pbpCnt",
     "1"
    ],
    [
     "pbpRsvNo",
     "SYNTHETIC-PBP"
    ],
    [
     "pnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "get_self_checkin_info": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.checkin.info.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDt",
     "20990102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "jrnySqno",
     "001"
    ]
   ]
  }
 ],
 "check_self_checkin_seat": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.checkin.psbFlg.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "qrcode",
     "SYNTHETIC-QR"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDd",
     "0102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "jrnySqno",
     "001"
    ]
   ]
  }
 ],
 "register_self_checkin": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.checkin.reg.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cpsNo",
     "SYNTHETIC-CPS"
    ],
    [
     "scarNo",
     "0017"
    ],
    [
     "seatNo",
     "5A"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDd",
     "0102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "jrnySqno",
     "001"
    ]
   ]
  }
 ],
 "cancel_self_checkin": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.checkin.cnc.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "saleWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "saleDt",
     "20990102"
    ],
    [
     "saleSqno",
     "1"
    ],
    [
     "tkRetPwd",
     "SYNTHETIC-RETURN"
    ],
    [
     "jrnySqno",
     "001"
    ]
   ]
  }
 ],
 "get_reservation_hold": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.ReservationList",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ]
   ]
  }
 ],
 "login[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "search_trains[lang-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_deposit_banks[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "AppVersion",
     "7.0.8"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu[lang-empty]": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_app_data[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_ticket_list[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "get_refund_commission[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "reserve[lang-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "pay_with_card[lang-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_limousine_schedules[lang-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ],
 "login[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "search_trains[lang-set]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_deposit_banks[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "AppVersion",
     "7.0.8"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu[lang-set]": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_app_data[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_ticket_list[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "get_refund_commission[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "reserve[lang-set]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "pay_with_card[lang-set]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_limousine_schedules[lang-set]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "lang",
     "SYNTHETIC-LANG"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ],
 "login[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "search_trains[app-version-none]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_deposit_banks[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu[app-version-none]": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_app_data[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_ticket_list[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "get_refund_commission[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "reserve[app-version-none]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "pay_with_card[app-version-none]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_limousine_schedules[app-version-none]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ],
 "login[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "search_trains[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_deposit_banks[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "AppVersion",
     "7.0.10"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu[app-version-7010]": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_app_data[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_ticket_list[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "get_refund_commission[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "reserve[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "pay_with_card[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_limousine_schedules[app-version-7010]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250722001"
    ],
    [
     "AppVersion",
     "7.0.10"
    ],
    [
     "Key",
     "SYNTHETIC-APP-KEY"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ],
 "login[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/MobileService.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "timeStamp",
     "4102444800000"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.common.code.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "code",
     "app.display.image"
    ],
    [
     "code",
     "app.menu.railpoint"
    ],
    [
     "code",
     "app.main.popup"
    ],
    [
     "code",
     "app.easyLogin.isShow"
    ],
    [
     "code",
     "app.korail.boss"
    ],
    [
     "code",
     "app.menu.buynow"
    ],
    [
     "code",
     "app.menu.lost112"
    ],
    [
     "code",
     "app.event.easyPay"
    ],
    [
     "code",
     "app.hndy.athn"
    ],
    [
     "code",
     "app.view.visibility"
    ],
    [
     "code",
     "app.menu.biz"
    ],
    [
     "code",
     "app.event.point"
    ],
    [
     "code",
     "app.var.data"
    ],
    [
     "code",
     "app.login.cphd"
    ],
    [
     "code",
     "app.illegal.report"
    ],
    [
     "code",
     "app.holiday.popup"
    ],
    [
     "code",
     "app.MaaS.test"
    ],
    [
     "code",
     "app.limousine.mainMsg"
    ],
    [
     "deviceWidth",
     "1440"
    ],
    [
     "deviceHeight",
     "3120"
    ],
    [
     "OSVersion",
     "37"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.login.Login",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "txtInputFlg",
     "2"
    ],
    [
     "txtMemberNo",
     "0000000000"
    ],
    [
     "txtPwd",
     "NEVMMWdrT3FoZ250aUVDOUM3TTlYU2lhMFVJK1dkU3Y0M25ESFBlUmlyWT0=\n"
    ],
    [
     "checkValidPw",
     "Y"
    ],
    [
     "idx",
     "1"
    ]
   ]
  }
 ],
 "search_trains[key-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_8"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.seatMovie.ScheduleView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "radJobId",
     "1"
    ],
    [
     "selGoTrain",
     "109"
    ],
    [
     "txtTrnGpCd",
     "109"
    ],
    [
     "txtGoStart",
     "출발시험역"
    ],
    [
     "txtGoEnd",
     "도착시험역"
    ],
    [
     "txtGoAbrdDt",
     "20990102"
    ],
    [
     "txtGoHour",
     "090000"
    ],
    [
     "txtPsgFlg_1",
     "1"
    ],
    [
     "txtPsgFlg_2",
     "0"
    ],
    [
     "txtPsgFlg_3",
     "0"
    ],
    [
     "txtPsgFlg_4",
     "0"
    ],
    [
     "txtPsgFlg_5",
     "0"
    ],
    [
     "txtSeatAttCd_2",
     "000"
    ],
    [
     "txtSeatAttCd_3",
     "000"
    ],
    [
     "txtSeatAttCd_4",
     "015"
    ],
    [
     "ebizCrossCheck",
     "N"
    ],
    [
     "srtCheckYn",
     "N"
    ],
    [
     "rtYn",
     "N"
    ],
    [
     "adjStnScdlOfrFlg",
     "N"
    ],
    [
     "mbCrdNo",
     "SYNTHETIC-MEMBER-CARD"
    ],
    [
     "qryDvCd",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_train_schedule[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.research.actualTrainSchedule.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "runDt",
     "20990102"
    ],
    [
     "trnNo",
     "90001"
    ]
   ]
  }
 ],
 "get_deposit_banks[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.dlay.dptnBank.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     ""
    ],
    [
     "AppVersion",
     "7.0.8"
    ]
   ]
  }
 ],
 "get_commuter_kind_menu[key-empty]": [
  {
   "method": "GET",
   "url": "https://api.example.invalid/classes/com.korail.mobile.push.cmtrKnd.do",
   "query": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "Key",
     ""
    ],
    [
     "cmtrKndCd",
     "SYNTHETIC-KIND"
    ]
   ],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": []
  }
 ],
 "get_app_data[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/file/CACHE/prdMobilePlusMain.cache",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "timeStamp",
     "1"
    ],
    [
     "srtCheckYn",
     "Y"
    ]
   ]
  }
 ],
 "get_ticket_list[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.myTicket.MyTicketNewList.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "txtIndex",
     "1"
    ],
    [
     "hiduserYn",
     "Y"
    ],
    [
     "h_page_no",
     "1"
    ]
   ]
  }
 ],
 "get_refund_commission[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.refunds.CommissionView",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "h_orgtk_ret_sale_dt",
     "20990102"
    ],
    [
     "h_orgtk_wct_no",
     "SYNTHETIC-WINDOW"
    ],
    [
     "h_orgtk_sale_sqno",
     "1"
    ],
    [
     "h_orgtk_ret_pwd",
     "SYNTHETIC-RETURN"
    ]
   ]
  }
 ],
 "reserve[key-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_14"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.certification.TicketReservation",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "x-dynapath-m-token": "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "txtMenuId",
     "11"
    ],
    [
     "txtJobId",
     "1101"
    ],
    [
     "hidFreeFlg",
     "N"
    ],
    [
     "txtStndFlg",
     "N"
    ],
    [
     "txtTotPsgCnt",
     "1"
    ],
    [
     "txtSeatAttCd1",
     "000"
    ],
    [
     "txtSeatAttCd2",
     "000"
    ],
    [
     "txtSeatAttCd3",
     "000"
    ],
    [
     "txtSeatAttCd4",
     "015"
    ],
    [
     "txtSeatAttCd5",
     "000"
    ],
    [
     "txtJrnyCnt",
     "1"
    ],
    [
     "txtCompaCnt1",
     "1"
    ],
    [
     "txtPsgTpCd1",
     "1"
    ],
    [
     "txtDiscKndCd1",
     "000"
    ],
    [
     "txtJrnyTpCd1",
     "11"
    ],
    [
     "txtJrnySqno1",
     "001"
    ],
    [
     "txtTrnNo1",
     "90001"
    ],
    [
     "txtTrnClsfCd1",
     "00"
    ],
    [
     "txtTrnGpCd1",
     "100"
    ],
    [
     "txtRunDt1",
     "20990102"
    ],
    [
     "txtDptDt1",
     "20990102"
    ],
    [
     "txtDptTm1",
     "090000"
    ],
    [
     "txtDptRsStnCd1",
     "9901"
    ],
    [
     "txtDptStnConsOrdr1",
     "1"
    ],
    [
     "txtDptStnRunOrdr1",
     "1"
    ],
    [
     "txtArvRsStnCd1",
     "9903"
    ],
    [
     "txtArvStnConsOrdr1",
     "3"
    ],
    [
     "txtArvStnRunOrdr1",
     "3"
    ],
    [
     "txtChgFlg1",
     "N"
    ],
    [
     "txtPsrmClCd1",
     "1"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "pay_with_card[key-empty]": [
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5101"
    ],
    [
     "sid",
     "service_1"
    ],
    [
     "aid",
     "act_18"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  },
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.payment.ReservationPayment",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "hidPnrNo",
     "SYNTHETIC-PNR"
    ],
    [
     "hidWctNo",
     "SYNTHETIC-WINDOW"
    ],
    [
     "hidTmpJobSqno1",
     "1"
    ],
    [
     "hidTmpJobSqno2",
     "2"
    ],
    [
     "hidRsvChgNo",
     "000"
    ],
    [
     "hidInrecmnsGridcnt",
     "1"
    ],
    [
     "hidStlMnsSqno1",
     "1"
    ],
    [
     "hidStlMnsCd1",
     "02"
    ],
    [
     "hidMnsStlAmt1",
     "1000"
    ],
    [
     "hidCrdInpWayCd1",
     "@"
    ],
    [
     "hidStlCrCrdNo1",
     "0000000000000000"
    ],
    [
     "hidVanPwd1",
     "00"
    ],
    [
     "hidCrdVlidTrm1",
     "9912"
    ],
    [
     "hidIsmtMnthNum1",
     "0"
    ],
    [
     "hidAthnDvCd1",
     "J"
    ],
    [
     "hidAthnVal1",
     "000101"
    ],
    [
     "hiduserYn",
     "Y"
    ]
   ]
  },
  {
   "method": "POST",
   "url": "https://queue.example.invalid/ts.wseq",
   "query": [
    [
     "opcode",
     "5004"
    ],
    [
     "key",
     "SYNTHETIC-QUEUE"
    ]
   ],
   "headers": {
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)",
    "accept-charset": "UTF-8",
    "context_type": "application/x-www-form-urlencoded;charset=UTF-8",
    "content-type": "application/x-www-form-urlencoded",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip"
   },
   "body": []
  }
 ],
 "get_limousine_schedules[key-empty]": [
  {
   "method": "POST",
   "url": "https://api.example.invalid/classes/com.korail.mobile.lmu.scdlQry.do",
   "query": [],
   "headers": {
    "user-agent": "korailtalk",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "JSESSIONID=SYNTHETIC-SESSION"
   },
   "body": [
    [
     "Device",
     "AD"
    ],
    [
     "Version",
     "250601003"
    ],
    [
     "AppVersion",
     "7.0.8"
    ],
    [
     "dptDt",
     "20990102"
    ],
    [
     "dptRsStnCd",
     "9901"
    ],
    [
     "arvRsStnCd",
     "9903"
    ],
    [
     "trnGpCd",
     "800"
    ],
    [
     "psrmClCd",
     "1"
    ],
    [
     "dptTm",
     "090000"
    ],
    [
     "trnNo",
     "90001"
    ],
    [
     "seatAttCd",
     "015"
    ],
    [
     "rsvSaleDvCd",
     "1"
    ]
   ]
  }
 ]
}""")
