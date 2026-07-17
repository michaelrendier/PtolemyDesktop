#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSvg import *
from PyQt6.QtSvgWidgets import *

import googlemaps, MySQLdb, socket, sys


from subprocess import PIPE, Popen
from datetime import datetime
try:
    from html2text import html2text as h2t
except ImportError:
    h2t = lambda x: x  # TODO:BUILD — install html2text
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
from urllib.request import build_opener
# TODO:BUILD — replace espeak with Philadelphos.ptolemy_tongue
from Pharos.PtolFace import PtolFace
from Pharos.PGui import PMainWindow






direction_results = \
    [
        {'bounds':
             {'northeast': {'lat': 29.9741039, 'lng': -90.03103270000001},
              'southwest': {'lat': 29.9192194, 'lng': -90.0868912}},
        'copyrights': 'Map data ©2018 Google',
        'legs':
             [
                {
                    'distance': {'text': '7.9 mi', 'value': 12668},
                    'duration': {'text': '19 mins', 'value': 1162},
                    'duration_in_traffic': {'text': '16 mins', 'value': 956},
                    'end_address': '422 Harmony St, New Orleans, LA 70115, USA',
                    'end_location': {'lat': 29.9192947, 'lng': -90.0837947},
                    'start_address': '1317 Lesseps St, New Orleans, LA 70117, USA',
                    'start_location': {'lat': 29.9674222, 'lng': -90.0318372},
                    'steps':
                        [
                            {
                                'distance': {'text': '0.2 mi', 'value': 304},
                                'duration': {'text': '1 min', 'value': 72},
                                'end_location': {'lat': 29.9700651, 'lng': -90.03103270000001},
                                'html_instructions': 'Head <b>north</b> on <b>Lesseps St</b> toward <b>N Villere St</b>',
                                'polyline': {'points': 'k_|uD~iodPqBc@mE_AqE}@'},
                                'start_location': {'lat': 29.9674222, 'lng': -90.0318372},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '1.8 mi', 'value': 2929},
                                'duration': {'text': '5 mins', 'value': 315},
                                'end_location': {'lat': 29.9733752, 'lng': -90.0608046},
                                'html_instructions': 'Turn <b>left</b> at the 3rd cross street onto <b>N Claiborne Ave</b>',
                                'maneuver': 'turn-left',
                                'polyline': {'points': '}o|uD|dodPk@bEg@tDk@|Dk@bEg@nDc@`Dc@tCa@|Cg@pDq@xEe@lDaA|GM~@]bC[|BUzA?BEZKl@In@EVEZCLANMv@In@YnBE\\i@zDk@|DKh@?dAL`FL`FJhE@\\?NLhELbFL~EJ~EDbALfFLbFH`DB|@'},
                                'start_location': {'lat': 29.9700651, 'lng': -90.03103270000001},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '1.9 mi', 'value': 3016},
                                'duration': {'text': '3 mins', 'value': 153},
                                'end_location': {'lat': 29.9550818, 'lng': -90.0819113},
                                'html_instructions': 'Take the ramp on the <b>left</b> onto <b>I-10 W</b>',
                                'polyline': {'points': 'sd}uD~~tdPHPDTFt@Dd@Bd@Bt@Bt@JrDLhF?TFfBBt@@XBXDZ?D@FBP@DBJDRBF?@?@@??@Lb@BDN\\HJJLHHNLPLVLPH@?`A`@f@Pb@PB@@?ZRHFv@j@ZT\\Bz@v@PNv@p@x@r@j@f@VTx@p@|ArAf@b@|@v@JHLLRNvAnAPLzCjCFFNLLLz@r@x@r@HHhA`AtAlAB@@@bA|@LH@@TRdA~@@?ZXfA~@~@x@@@lAdAbA|@jCzB@?zCjCHFPP`Az@zBlBvE~D|@v@f@b@@@PNlAbA|@t@NNdBzAn@h@v@p@h@b@r@r@LN^d@V`@HNNVHJDDBF\\v@'},
                                'start_location': {'lat': 29.9733752, 'lng': -90.0608046},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '0.4 mi', 'value': 621},
                                'duration': {'text': '1 min', 'value': 38},
                                'end_location': {'lat': 29.9522188, 'lng': -90.0868912},
                                'html_instructions': 'Take the <b>U.S. 90 business W</b> exit on the <b>left</b> toward <b>Westbank</b>/<b>Claiborne Avenue</b>',
                                'maneuver': 'ramp-left',
                                'polyline': {'points': 'gryuD|bydPd@`A^bAZhANn@Pz@N|@@L?@BL?@?@DZ@N?@LhABV?BB\\?@@LLp@@@?BJb@?@Pp@J\\@BVd@b@j@b@d@XR\\PXJPH@?B@PFD@JBLBD@bAH'},
                                'start_location': {'lat': 29.9550818, 'lng': -90.0819113},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '1.2 mi', 'value': 1906},
                                'duration': {'text': '2 mins', 'value': 118},
                                'end_location': {'lat': 29.9413938, 'lng': -90.07214610000001},
                                'html_instructions': 'Keep <b>left</b> and merge onto <b>US-90 BUS W</b>',
                                'maneuver': 'keep-left',
                                'polyline': {'points': 'k`yuD`bzdPp@EB?\\EJCz@S@?~@]@A`@Q@?^UDCbAm@HGLKPONM@A?A@A@ABABCBCBC@AFGBC@AFG@?@CBCRQVUjAiABCj@g@VUBCDEDCZ]HI@A@AX[n@cADG@CHOJQBG@ADKTc@FKDIFMRa@FKFMDGDIP]JQZ}@vC_Fj@mAb@_Ad@cABEx@}A\\q@BGXi@HS@Ap@{Ah@eAJU`@y@?ADIBIP]p@_B@EFOnAmCt@}AbAwB~@qBjBcEVi@Te@N[FOHMLQf@iA`@{@'},
                                'start_location': {'lat': 29.9522188, 'lng': -90.0868912},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '0.3 mi', 'value': 443},
                                'duration': {'text': '1 min', 'value': 47},
                                'end_location': {'lat': 29.9390935, 'lng': -90.0684299},
                                'html_instructions': 'Take exit <b>11</b> toward <b>Tchoupitoulas St</b>/<b>S Peters St</b>',
                                'maneuver': 'ramp-right',
                                'polyline': {'points': 'u|vuD|ewdP^e@@AFIRU?APUPQNOJK@CZc@T[Zm@@A?AL[@CBELa@\\cAh@sA`BmDTi@Xk@'},
                                'start_location': {'lat': 29.9413938, 'lng': -90.07214610000001},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '0.1 mi', 'value': 195},
                                'duration': {'text': '1 min', 'value': 39},
                                'end_location': {'lat': 29.9380873, 'lng': -90.06677930000001},
                                'html_instructions': 'Merge onto <b>Calliope St</b>',
                                'maneuver': 'merge',
                                'polyline': {'points': 'invuDtnvdPLSTUFI@E\\k@JW@?r@}Ad@cARi@'},
                                'start_location': {'lat': 29.9390935, 'lng': -90.0684299},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '0.3 mi', 'value': 453},
                                'duration': {'text': '1 min', 'value': 63},
                                'end_location': {'lat': 29.93403859999999, 'lng': -90.0663225},
                                'html_instructions': 'Turn <b>right</b> onto <b>Tchoupitoulas St</b>',
                                'maneuver': 'turn-right',
                                'polyline': {'points': 'ahvuDjdvdPXARC@?d@EPAz@E^CjCAh@?pAMfCQ\\E|@IxBQ'},
                                'start_location': {'lat': 29.9380873, 'lng': -90.06677930000001},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '0.4 mi', 'value': 721},
                                'duration': {'text': '1 min', 'value': 68},
                                'end_location': {'lat': 29.9277401, 'lng': -90.06810829999999},
                                'html_instructions': 'Continue straight onto <b>Religious St</b>',
                                'maneuver': 'straight',
                                'polyline': {'points': 'wnuuDnavdPxDl@fEz@~Dx@jEv@bEv@~Dz@xAT'},
                                'start_location': {'lat': 29.93403859999999, 'lng': -90.0663225},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '371 ft', 'value': 113},
                                'duration': {'text': '1 min', 'value': 16},
                                'end_location': {'lat': 29.9270182, 'lng': -90.0672866},
                                'html_instructions': 'Turn <b>left</b> onto <b>Felicity St</b>',
                                'maneuver': 'turn-left',
                                'polyline': {'points': 'kgtuDtlvdPnCcD'},
                                'start_location': {'lat': 29.9277401, 'lng': -90.06810829999999},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '1.1 mi', 'value': 1770},
                                'duration': {'text': '3 mins', 'value': 185},
                                'end_location': {'lat': 29.9192194, 'lng': -90.0826498},
                                'html_instructions': 'Turn <b>right</b> onto <b>Tchoupitoulas St</b>',
                                'maneuver': 'turn-right',
                                'polyline': {'points': '{btuDpgvdPt@NnBb@XDRHHFJJPTV`@p@x@n@~@t@fA~@xAzBnDVb@NTLTVh@Zv@@@FPHTdBjEvAtDVl@N`@Rh@XhAR|@|@tDz@tDv@zD`A~DbBpHx@zD|@tDn@tCH`@'},
                                'start_location': {'lat': 29.9270182, 'lng': -90.0672866},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '289 ft', 'value': 88},
                                'duration': {'text': '1 min', 'value': 17},
                                'end_location': {'lat': 29.9198801, 'lng': -90.08314419999999},
                                'html_instructions': 'Turn <b>right</b> onto <b>Ninth St</b>',
                                'maneuver': 'turn-right',
                                'polyline': {'points': 'crruDpgydPcC`B'},
                                'start_location': {'lat': 29.9192194, 'lng': -90.0826498},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '279 ft', 'value': 85},
                                'duration': {'text': '1 min', 'value': 20},
                                'end_location': {'lat': 29.9194925, 'lng': -90.0839},
                                'html_instructions': 'Turn <b>left</b> at the 1st cross street onto <b>St Thomas St</b>',
                                'maneuver': 'turn-left',
                                'polyline': {'points': 'gvruDrjydPn@zALXN`@'},
                                'start_location': {'lat': 29.9198801, 'lng': -90.08314419999999},
                                'travel_mode': 'DRIVING'
                            },
                            {
                                'distance': {'text': '79 ft', 'value': 24},
                                'duration': {'text': '1 min', 'value': 11},
                                'end_location': {'lat': 29.9192947, 'lng': -90.0837947},
                                'html_instructions': 'Turn <b>left</b> onto <b>Harmony St</b><div style="font-size:0.9em">Destination will be on the right</div>',
                                'maneuver': 'turn-left',
                                'polyline': {'points': 'ysruDjoydPf@U'},
                                'start_location': {'lat': 29.9194925, 'lng': -90.0839},
                                'travel_mode': 'DRIVING'
                            }
                        ],
                    'traffic_speed_entry': [],
                    'via_waypoint': []
                }
            ],
        'overview_polyline': {'points': 'k_|uD~iodP_IcBqE}@k@bEsArJsArJgAvHiAnIgDdVqBrNcAnHuAxJKh@?dAZbMLfFh@|Sl@nVL~ENf@LzAFzA\\hNPpEPlAJ`@Ph@Xh@v@r@lBx@pAd@xB|A\\Bz@v@PNtDbD|F`FjIfHlHnG|IvHxO`NxQtOdDtC`BtA`AbAv@fAXf@NP`@~@dAdCj@xBb@hCJ~@VrCZzA^tAVd@b@j@|@x@jAf@f@NRDbAHp@E`@EfAWbA_@b@Qd@YlAu@^[RSHGVWdGyFBCX[n@cADGJSVg@j@gAh@cAVg@f@oAvC_Fj@mAhAcC~A}CnDsHlAqCnCaG~HwPt@{A`@{@^e@HKRWr@w@~@oAj@mAp@oBh@sA`BmDn@uAb@i@HOh@cAzAaDRi@XATCrCQtDAxE_@zAOxBQxDl@fKtBnKnB~Dz@xATnCcDt@NhCh@\\P\\`@V`@p@x@dBfCzDhGlAxBtGrPRh@XhApArFrBpJdDpNvBpJx@vDcC`Bn@zA\\z@f@U'},
        'summary': 'N Claiborne Ave',
        'warnings': [],
        'waypoint_order': []
        }
    ]

geocode_results = \
    [
        {
            'address_components':
                [
                    {
                        'long_name': 'Bishop',
                        'short_name': 'Bishop',
                        'types': ['locality', 'political']
                    },
                    {
                        'long_name': 'Inyo County',
                        'short_name': 'Inyo County',
                        'types': ['administrative_area_level_2', 'political']
                    },
                    {
                        'long_name': 'California',
                        'short_name': 'CA',
                        'types': ['administrative_area_level_1', 'political']
                    },
                    {
                        'long_name': 'United States',
                        'short_name': 'US',
                        'types': ['country', 'political']
                    },
                    {
                        'long_name': '93514',
                        'short_name': '93514',
                        'types': ['postal_code']
                    }
                ],
            'formatted_address': 'Bishop, CA 93514, USA',
            'geometry':
                {
                    'bounds':
                        {
                            'northeast': {'lat': 37.37932980000001, 'lng': -118.3815189},
                            'southwest': {'lat': 37.3536718, 'lng': -118.4141921}
                        },
                    'location': {'lat': 37.3614238, 'lng': -118.3996636},
                    'location_type': 'APPROXIMATE',
                    'viewport':
                        {
                            'northeast': {'lat': 37.37932980000001, 'lng': -118.3815189},
                            'southwest': {'lat': 37.3536718, 'lng': -118.4141921}
                        }
                },
            'place_id': 'ChIJB2SmngEWvoARFonplU0ezRM',
            'types': ['locality', 'political']
        }
    ]

geolocate_results = \
    {
        'accuracy': 939.0,
        'location':
            {
                'lat': 29.968278599999998,
                'lng': -90.0352144
            }
    }

elevation_results = \
    [
        {
            'elevation': 1281.799560546875,
            'location': {'lat': 37.37908, 'lng': -118.42044},
            'resolution': 9.543951988220215
        }
    ]

places_nearby_results = \
    {
        'html_attributions': [],
        'results':
            [
                {
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.2541598,
                                    'lng': -118.3765372
                                },
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.25571477989271,
                                            'lng': -118.3751740201073
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.25301512010726,
                                            'lng': -118.3778736798927
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/geocode-71.png',
                    'id': '8e3f2e8793d291c37fa99329ccd270451ccc0391',
                    'name': "Keough's Hot Springs",
                    'opening_hours': {'open_now': False},
                    'photos':
                        [
                            {
                                'height': 3036,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/118429996650994678491/photos">Mike E.</a>'
                                    ],
                                'photo_reference': 'CmRaAAAAdDCn3wyB7q02q4ppN8D3xw_H9yNcylY8ajfMJ3pwh4jTTs3z3YtHRYHmGQ333aLS_4ig2yyK-cgAwW6J1yG7mLt0mmKldxT5STVGf46KpLjMjoXvM5LOXNP78O8ICtQsEhAZr2Ny_KpK4Lj68MSrL3WuGhQbeNIuLie1N2ORmcrVVnYeZ7uQ7g',
                                'width': 4048
                            }
                        ],
                    'place_id': 'ChIJka9tAnU5voARD-wLRLxeeiY',
                    'plus_code':
                        {
                            'compound_code': '7J3F+M9 Wilkerson, California',
                            'global_code': '85937J3F+M9'
                        },
                    'rating': 4,
                    'reference': 'CmRbAAAAqC90TDvpDx7wp2rFiJZ1b5Yp5bkdLJozuDK6sr9vhvjNEgssOOBwZ_JHAiN9BDvrMY8BlrKqnVKGdCQRCTJhEiOOTmQGXylL4sGYZU7u-CZq-HSYzKrne97kmcz-0fLpEhBZs2Lp6RIL_Zp2379RXSp5GhTIAAJeuYusfHhwhfqJCHWNmF9vfw',
                    'scope': 'GOOGLE',
                    'types':
                        [
                            'natural_feature',
                            'point_of_interest',
                            'establishment'
                        ],
                    'vicinity': '800 Keough Hot Springs Rd, Bishop'
                },
                {
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.2567,
                                    'lng': -118.3726712
                                },
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.25804982989271,
                                            'lng': -118.3713213701073
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.25535017010727,
                                            'lng': -118.3740210298927
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/geocode-71.png',
                    'id': 'e1b088594c11e4439a36cb7c0673779e211b606d',
                    'name': "Keogh's Hot Springs",
                    'photos':
                        [
                            {
                                'height': 3024,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/105376246064971466964/photos">A Google User</a>'
                                    ],
                                'photo_reference': 'CmRaAAAADfvryC2BL5hf_XzaO-fbqccYVUZ7rm5-qQXMUXi1_Y1Al6PGw5Wo3QTAECBoGvJnhG1wM8sCLDBPbD6zngcxFnMDN5eKTQAnwrVXIYq8AaLioKGf6VbU3iXR8Z3NCxbxEhArfMmULhq2rcMk6YeV8HOJGhQFhVSwKwjHaMb2ULJO1NadOaXL1Q',
                                'width': 4032
                            }
                        ],
                    'place_id': 'ChIJm0cU_nQ5voAR64vfCIe7pCI',
                    'plus_code':
                        {
                            'compound_code': '7J4G+MW Wilkerson, California',
                            'global_code': '85937J4G+MW'
                        },
                    'rating': 4.3,
                    'reference': 'CmRbAAAASkvTNJIDZfOT7Kr_JPUxhCKwITRXJ9OWO759IMIbIwS2gSuKPX6RDgyqNKh6ikXwdnbOJOqkbIjFQMHWsBBXzZ216uLv5seoha03oM07rynjJiCpYMDPuG2C3gDsZzDtEhDa18YQQxFF4gguvvVUZyJMGhQi0r0jWh96VrQyz1dM28lvH2oPoQ',
                    'scope': 'GOOGLE',
                    'types':
                        [
                            'natural_feature',
                            'point_of_interest',
                            'establishment'
                        ], 'vicinity': '801-, 869 Keough Hot Springs Rd, Bishop'
                },
                {
                    'geometry':
                         {
                             'location':
                                 {
                                     'lat': 37.25620300000001,
                                     'lng': -118.372627
                                 },
                             'viewport':
                                 {
                                     'northeast':
                                         {
                                             'lat': 37.2650835,
                                             'lng': -118.3566196
                                         },
                                     'southwest':
                                         {
                                             'lat': 37.2473214,
                                             'lng': -118.3886344
                                         }
                                 }
                         },
                        'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/geocode-71.png',
                        'id': '1fc5a78eb3206ac7036cc2164b7eebee9b90af58',
                        'name': 'Keough Hot Springs',
                        'photos':
                            [
                                {
                                    'height': 1536,
                                    'html_attributions':
                                        [
                                            '<a href="https://maps.google.com/maps/contrib/103922534832997833340/photos">Manny Onanda</a>'
                                        ],
                                    'photo_reference': 'CmRaAAAA6mKJ73gLJxE70iFJP9CIO2tOw-1mnsMQ9JiOtGu1ujzyCW2E8EXN1hv34jHpViczhjj-APVfhfyO_8wP-JdQCgDhGe9qdo5g4eRkF1e9pV7-Oo9zZGotzqOl2qKV-12CEhBaO61Us3nOyF9PEChyOd0mGhSYpiWkxYUHIwVhePNar_Z-18UTSA',
                                    'width': 1536
                                }
                            ],
                        'place_id': 'ChIJA3oIX3Q5voARLNrIk01H0kg',
                        'reference': 'CmRbAAAA9ia-dKBjCMEdkempbpexQWkb-tNj_bXrXXctoMJeR99GPxPByoWi5Tos416gWc7zjKdprcyDD9zuH5KRxptX23N79VI6I_oP7-K21vfOV_u9En0oKt2fnD0wAgMfgtHHEhBNqcO9Ed8MwpoWpW3vNTzSGhRXuMGj7Jf_iLkd8OQgZxDYbi1XUg',
                        'scope': 'GOOGLE',
                        'types':
                            [
                                'locality',
                                'political'
                            ],
                        'vicinity': 'California 93514, USA'
                },
                {
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.3609473,
                                    'lng': -118.4019902
                                },
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.36250742989272,
                                            'lng': -118.4004946201073
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.35980777010727,
                                            'lng': -118.4031942798927
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/shopping-71.png',
                    'id': '4506fa5a68edb0e2aa5591c8c15b1a648e3fbc6a',
                    'name': 'Giggle Springs Too',
                    'opening_hours':
                        {
                            'open_now': False
                        },
                    'photos':
                        [
                            {
                                'height': 2268,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/114854246201320697713/photos">Raquel Felix</a>'
                                    ],
                                'photo_reference': 'CmRaAAAAeEvfkB_-5kQp7o9rIafNHVrh08SmPW0YRKaWd4EcJpgpMxWdrZCIXFw59W9mvLlkWTMM_3SyC8vuGc7lzb5PWBcQflbs0tQoubAAuCxr4j2TZPyW2GN6U522yzqf7XiSEhC8aEvjsi11LFfTJM9tZCLPGhRTYQgHXqvlJS9LMtLpOldAKU6Egw',
                                'width': 4032
                            }
                        ],
                    'place_id': 'ChIJp42TVvg9voARyrnYnOcGkFE',
                    'plus_code':
                        {
                            'compound_code': '9H6X+96 Bishop, California',
                            'global_code': '85939H6X+96'
                        },
                    'rating': 2,
                    'reference': 'CmRbAAAAJu6zD0WpPCRlCjb6ib7UCKekjgnCcdO_m11QZrZXUPbh8PHhQJY5J1JoKSAiaOhX1xGshuiNQbtlKuojugszdL3SulU5e-LyAjTWIG9gaOHwEBFnafPJOY-j7O8lxqu1EhAV4-qmz8ExHKz1oHLZkv1YGhT98XVrd4VEyqm5nvTjwQyuaQEqQg',
                    'scope': 'GOOGLE',
                    'types':
                        [
                            'convenience_store',
                            'store',
                            'food',
                            'point_of_interest',
                            'establishment'
                        ],
                    'vicinity': '710 W Line St, Bishop'
                },
                {
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.2550802,
                                    'lng': -118.3769989
                                },
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.25620407989273,
                                            'lng': -118.3754469701072
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.25350442010728,
                                            'lng': -118.3781466298927
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/generic_business-71.png',
                    'id': '59422673011329269943e38a875bcf3eb0a59b47',
                    'name': 'Wildcare Eastern Sierra',
                    'opening_hours':
                        {
                            'open_now': False
                        },
                    'photos':
                        [
                            {
                                'height': 2988,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/116487684168917592050/photos">harry yun</a>'
                                    ],
                                'photo_reference': 'CmRaAAAA7gIdeL3c7X9exdTB-7D6bRA1y2VBDSFeeB6_gRHIHRxAQtf9QKstbJFTDC2t2HK2jblS11RD29oduKPkvyElk4eRyjN4_o3nSemdima4x79yY5M46ufj4mXtl9W2J8WLEhCwfuhR9d3gNlsD9TWULNYHGhTE8OHOST81c54FZyNQ-gesNmfa7Q',
                                'width': 5312
                            }
                        ],
                    'place_id': 'ChIJka9tAnU5voAReKZS74rbZy0',
                    'plus_code':
                        {
                            'compound_code': '7J4F+26 Wilkerson, California',
                            'global_code': '85937J4F+26'
                        },
                    'rating': 4.3,
                    'reference': 'CmRbAAAAjXAJfH-sh4kZAVaGaPF_9pYcNnVoU_Jq0TppNPTddxIEw7lEBIr-YXS2Y-bzbGAB7frOH1dm9XXN2jodqDtuqvQAHYEtNdx-f50gy6fTqipTe7H9KCzGPLymKRxGTYCYEhAWMOp4IHKR6qRTtxNTo63bGhTgGYvF4eUB8Se0yFr90hTNeTftnA',
                    'scope': 'GOOGLE',
                    'types':
                        [
                            'point_of_interest',
                            'establishment'
                        ],
                    'vicinity': '800 Keough Hot Springs Rd, Bishop'
                }
            ],
        'status': 'OK'
    }

timezone_results = \
    {
        'dstOffset': 3600,
        'rawOffset': -21600,
        'status': 'OK',
        'timeZoneId': 'America/Chicago',
        'timeZoneName': 'Central Daylight Time'
    }

places_results = \
    {
        'html_attributions': [],
        'results':
            [
                {
                    'formatted_address': '585 W Line St, Bishop, CA 93514, USA',
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.3615943,
                                    'lng': -118.4003923
                                },
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.36283217989272,
                                            'lng': -118.3990416701073
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.36013252010728,
                                            'lng': -118.4017413298928
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/post_office-71.png',
                    'id': 'de18a9f6a2cc99aa44cd9ec31cf1c6ee76091e28',
                    'name': 'United States Postal Service',
                    'opening_hours':
                        {
                            'open_now': False
                        },
                    'photos':
                        [
                            {
                                'height': 3024,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/110792431341706254499/photos">India Clamp</a>'
                                    ],
                                'photo_reference': 'CmRaAAAAfeG8ydtRCsHEsjyBTjMqu9urKC3Gj1dU4hPh8FATZh1khixF2BpgHVy46hnMi0-LIdkJcf-5_9T3zCi5QziHwD4vgK43VRWPFyf7EojiPK-HQRazZzASaFUD564J6DEhEhB6XPQPhGVA7hyGP5One-kxGhTE5-cFGVX-Kl9WbZNRkxCrzMF5BA',
                                'width': 4032
                            }
                        ],
                    'place_id': 'ChIJX0yo5_g9voARp4Kpub7PnlE',
                    'plus_code':
                        {
                            'compound_code': '9H6X+JR Bishop, California',
                            'global_code': '85939H6X+JR'
                        },
                    'rating': 2.9,
                    'reference': 'CmRbAAAAf_8jPbLQYRW1dMbbz6_-haaqA6lCZGWWauo-gFnPUTkeMoKFIuV-VBNxBpvtOtxir9tSTT2zsYE34P1vnwx9DlQ_VMi_l8rr7DTe9KsPJJv921_NY42mFkrSQq8Mqq3tEhBk7zuDt40JIpyeHly4c-YrGhTheEQHmAm3JP34cnqcy3o1JYasqg',
                    'types':
                        [
                            'post_office',
                            'finance',
                            'point_of_interest',
                            'establishment'
                        ]
                },
                {
                    'formatted_address': '140 N Main St, Big Pine, CA 93513, USA',
                    'geometry':
                        {
                            'location':
                                {
                                    'lat': 37.16701990000001,
                                    'lng': -118.2892353},
                            'viewport':
                                {
                                    'northeast':
                                        {
                                            'lat': 37.16836862989273,
                                            'lng': -118.2880398201072
                                        },
                                    'southwest':
                                        {
                                            'lat': 37.16566897010728,
                                            'lng': -118.2907394798927
                                        }
                                }
                        },
                    'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/post_office-71.png',
                    'id': '73de6f00d571a95279d4da5de26a1d56a701e648',
                    'name': 'United States Postal Service',
                    'opening_hours':
                        {
                            'open_now': False
                        },
                    'photos':
                        [
                            {
                                'height': 1025,
                                'html_attributions':
                                    [
                                        '<a href="https://maps.google.com/maps/contrib/114893327318400598855/photos">United States Postal Service</a>'
                                    ],
                                'photo_reference': 'CmRaAAAAvl3jaZaTggGRpnoLXhpenbTgRxfCsISu6lRYRfrIcqdW8MT9U-w6C3yRkZg4818pWRWDEa1hvWIrhD0n_UwHAS5DyJ42QNXUMqGymsJplGTXiWWhONQ7ObiF-nLoVOEKEhCdHA4PAYJiMurl1oV2_CyjGhTpWQbidUsKFRDtX_k279mfqhC70A',
                                'width': 1025
                            }
                        ],
                    'place_id': 'ChIJO4WSQOVJvoARmDCUZcPMsEQ',
                    'plus_code':
                        {
                            'compound_code': '5P86+R8 Big Pine, California',
                            'global_code': '85935P86+R8'
                        },
                    'reference': 'CmRbAAAAO7olBzrNoqttSXYG7LQmoEmf1fL0BHwQymBxFDTzNMOR1s_F09PUR0kqiVmLj2kg8WIH8uaEP0enbiFVB4PBFZySCA9Rh53c7HtXRnS8XR6_IJ51X7mv6gyIZzhxR96IEhDMFEu2NXzg899PEo5uxHwBGhTQ08J5cw7xdX_32wgeHFf3UKpmnw',
                    'types':
                        [
                            'post_office',
                            'finance',
                            'point_of_interest',
                            'establishment'
                        ]
                }
            ],
        'status': 'OK'
    }

place_results = \
    {
        'html_attributions': [],
        'result':
            {'address_components':
                 [
                     {
                         'long_name': '585',
                         'short_name': '585',
                         'types':
                             [
                                 'street_number'
                             ]
                     },
                     {
                         'long_name': 'West Line Street',
                         'short_name': 'W Line St', 'types':
                         [
                             'route'
                         ]
                     },
                     {
                         'long_name': 'Bishop',
                         'short_name': 'Bishop',
                         'types':
                             [
                                 'locality',
                                 'political'
                             ]
                     },
                     {
                         'long_name': 'Inyo County',
                         'short_name': 'Inyo County',
                         'types':
                             [
                                 'administrative_area_level_2',
                                 'political'
                             ]
                     },
                     {
                         'long_name': 'California',
                         'short_name': 'CA',
                         'types':
                             [
                                 'administrative_area_level_1',
                                 'political'
                             ]
                     },
                     {
                         'long_name': 'United States',
                         'short_name': 'US',
                         'types':
                             [
                                 'country',
                                 'political'
                             ]
                     },
                     {
                         'long_name': '93514',
                         'short_name': '93514',
                         'types':
                             [
                                 'postal_code'
                             ]
                     }
                 ],
                'adr_address': '<span class="street-address">585 W Line St</span>, <span class="locality">Bishop</span>, <span class="region">CA</span> <span class="postal-code">93514</span>, <span class="country-name">USA</span>',
                'formatted_address': '585 W Line St, Bishop, CA 93514, USA',
                'formatted_phone_number': '(800) 275-8777',
                'geometry':
                    {
                        'location':
                            {
                                'lat': 37.3615943,
                                'lng': -118.4003923
                            },
                        'viewport':
                            {
                                'northeast':
                                    {
                                        'lat': 37.3628313302915,
                                        'lng': -118.3990425197085
                                    },
                                'southwest':
                                    {
                                        'lat': 37.3601333697085,
                                        'lng': -118.4017404802915
                                    }
                            }
                    },
                'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/post_office-71.png',
                'id': 'de18a9f6a2cc99aa44cd9ec31cf1c6ee76091e28',
                'international_phone_number': '+1 800-275-8777',
                'name': 'United States Postal Service',
                'opening_hours':
                    {'open_now': False,
                     'periods':
                         [
                             {
                                 'close':
                                     {
                                         'day': 1,
                                         'time': '1600'
                                     },
                                 'open':
                                     {
                                         'day': 1,
                                         'time': '0900'
                                     }
                             },
                             {
                                 'close':
                                     {
                                         'day': 2,
                                         'time': '1600'
                                     },
                                 'open':
                                     {
                                         'day': 2,
                                         'time': '0900'
                                     }
                             },
                             {
                                 'close':
                                     {
                                         'day': 3,
                                         'time': '1600'
                                     },
                                 'open':
                                     {
                                         'day': 3,
                                         'time': '0900'
                                     }
                             },
                             {
                                 'close':
                                     {
                                         'day': 4,
                                         'time': '1600'
                                     },
                                 'open':
                                     {
                                         'day': 4,
                                         'time': '0900'
                                     }
                             },
                             {
                                 'close':
                                     {
                                         'day': 5,
                                         'time': '1600'
                                     },
                                 'open':
                                     {
                                         'day': 5,
                                         'time': '0900'
                                     }
                             },
                             {
                                 'close':
                                     {
                                         'day': 6,
                                         'time': '1300'
                                     },
                                 'open':
                                     {
                                         'day': 6,
                                         'time': '0900'
                                     }
                             }
                         ],
                     'weekday_text':
                         [
                             'Monday: 9:00 AM – 4:00 PM',
                             'Tuesday: 9:00 AM – 4:00 PM',
                             'Wednesday: 9:00 AM – 4:00 PM',
                             'Thursday: 9:00 AM – 4:00 PM',
                             'Friday: 9:00 AM – 4:00 PM',
                             'Saturday: 9:00 AM – 1:00 PM',
                             'Sunday: Closed'
                         ]
                     },
                'photos':
                    [
                        {
                            'height': 3024,
                            'html_attributions':
                                [
                                    '<a href="https://maps.google.com/maps/contrib/110792431341706254499/photos">India Clamp</a>'
                                ],
                            'photo_reference': 'CmRaAAAA56tpW3S-SYh4fc78wDyHtABGGWzIUPDmwYg4l-vdtHre_i71fhRUrEp7G--1kyDnKC5rgp5VWak0xkexb3RZ9tZZBWJVVdYm6mKb2DFa1-2rbY9Ocad0e5es3AWIFyTFEhCcXK5T2WbsfB9vc0t1Uo0EGhSVup2Nw9L3BvoIkPu_cq02yYB1cQ',
                            'width': 4032
                        },
                        {
                            'height': 3024,
                            'html_attributions':
                                [
                                    '<a href="https://maps.google.com/maps/contrib/110792431341706254499/photos">India Clamp</a>'
                                ],
                            'photo_reference': 'CmRaAAAADzpq4pTYf0BryuQw2IIaq33JhcjAGWSuhMosNFA8xLCO3MGyAteiC9hrd-jALh96beARmO-puaB6_gGY_O-7plUOOMgjKVSpJFlW-kmItWngrJBP-zaLszX_jjopk1rvEhAHuSOhAyvtice2Lg0KxjbWGhTC30oqExo8OoyPJnyuwcVkbyyL2A',
                            'width': 4032
                        },
                        {
                            'height': 3024,
                            'html_attributions':
                                [
                                    '<a href="https://maps.google.com/maps/contrib/108925670703726883562/photos">Justin Norcross</a>'
                                ],
                            'photo_reference': 'CmRaAAAAsEaAIUCIiWyxvsXcuSvYDfDo3T1ch39NO42VJpMlPMiIe5IOU1P5gp7szLrfmIpk_96R0zdvO2-S7ccDs8L-Cn9fRq1D4XJ0BvUhiHnvNqQy0P3coH9SW17wV5GzMRt9EhAwQL8HeoDuPFY97EjI_8jmGhTZvd1ycG1ffsNITGvz0W1bBuxxhQ',
                            'width': 4032
                        },
                        {
                            'height': 1656,
                            'html_attributions':
                                [
                                    '<a href="https://maps.google.com/maps/contrib/110792431341706254499/photos">India Clamp</a>'
                                ],
                            'photo_reference': 'CmRaAAAA7YuS8qfOpZWtWxrijeFtBOw2vgmae6nZMhyVr4FHL26OPPCkG06BdQ0fgIcv0h9hrqvowoUoEKS80Q4um0JGRbrIjfCwjooWT8UWo4Rf-i_icgS-GiJc9eKT0aIsQeqwEhDP5KNoZT1VBzVhQhQoFYs7GhQM0Dc0G0kiE8r5JGu4Zwe8Gc79Wg',
                            'width': 1242
                        },
                        {
                            'height': 1025,
                            'html_attributions':
                                [
                                    '<a href="https://maps.google.com/maps/contrib/105822166938124761371/photos">United States Postal Service</a>'
                                ],
                            'photo_reference': 'CmRaAAAAh28Umuk43L9t3k6pGUeGqjAOI-zsbhwc-hVrjM_mQzC-0imxrSd3Zinht1fC8pbSrF8N62-XgN7HzCxpNrWdM1yGxZ1Nx6YlmkbhJHx5XneZs7OySCvQ33vmKDFFQwF_EhDH97iYpDS1_k_FWRDrG5X1GhTJn28LoE9qiKFi6i5QmbWctqYKIQ',
                            'width': 1025
                        }
                    ],
                'place_id': 'ChIJX0yo5_g9voARp4Kpub7PnlE',
                'plus_code':
                    {
                        'compound_code': '9H6X+JR Bishop, California, United States',
                        'global_code': '85939H6X+JR'
                    },
                'rating': 2.9,
                'reference': 'CmRRAAAA-w5tnhnAon70LKGsXjvdWbR3ZKEfguRqRmZWy2OzpasHMRm5ltAazi_JGkcHVB2R6cUVvtwPYRe95Jiyv653EVMW_GTQyVTCCnloonVhTFiwQN8RCz4CgQjd1Z2CgXpHEhBPFgnPP0FIyhDieAa6x8WIGhR7bIXPSwaMfFoCfWjhth5_xNmLSQ',
                'reviews':
                    [
                        {
                            'author_name': 'J. Guffey',
                            'author_url': 'https://www.google.com/maps/contrib/111440740139224103667/reviews',
                            'language': 'en',
                            'profile_photo_url': 'https://lh3.googleusercontent.com/-iTeAd9qC_m8/AAAAAAAAAAI/AAAAAAAAABo/26sNFMZ-CTU/s128-c0x00000000-cc-rp-mo-ba2/photo.jpg',
                            'rating': 1,
                            'relative_time_description': '2 months ago',
                            'text': "Very disappointed in the staff.  I was informed that they no longer offer the clear packing tape with priority shipping, so I went to my car and found some duct tape. The clerk watched me secure my package for 10 minutes, then waited in line, THEN she tells me she can't accept a package with duct tape!!  It was a furious waste of my time.",
                            'time': 1525115526
                        },
                        {
                            'author_name': 'India Clamp',
                            'author_url': 'https://www.google.com/maps/contrib/110792431341706254499/reviews',
                            'language': 'en',
                            'profile_photo_url': 'https://lh3.googleusercontent.com/-1P-a4Bwx7Q8/AAAAAAAAAAI/AAAAAAAAfbc/BHAaEZNdkq0/s128-c0x00000000-cc-rp-mo-ba6/photo.jpg',
                            'rating': 3,
                            'relative_time_description': '11 months ago',
                            'text': "Charming town and area. Don't take the Post Office for granted as Passport Services are offered (see website).\n\nDoor was open and I was delighted to observe this Post Office listing John F. Kennedy (who was President at the time) and the Postmaster.\n\nThanks to the town for the blooming flowers hanging on lampposts in baskets ----keeping me looking up.",
                            'time': 1500095692
                        },
                        {
                            'author_name': 'Ashlyn Tingley',
                            'author_url': 'https://www.google.com/maps/contrib/102468718726493500985/reviews',
                            'language': 'en',
                            'profile_photo_url': 'https://lh6.googleusercontent.com/-bfwdW9C4NBU/AAAAAAAAAAI/AAAAAAAAAY4/QT-3vXEZbZk/s128-c0x00000000-cc-rp-mo/photo.jpg',
                            'rating': 1,
                            'relative_time_description': '6 months ago',
                            'text': "Terrible service, they can not answer the simplest of questions. A man named Ben was very rude twice now I've called. I'm suprised they even answer the phone. I have a hard time knowing My mail has to go through this post office because of how idiotic the people are. I'm very disappointed on the people they choose to hire.",
                            'time': 1513901576
                        },
                        {
                            'author_name': 'Joel Krause',
                            'author_url': 'https://www.google.com/maps/contrib/103582314862313441675/reviews',
                            'language': 'en',
                            'profile_photo_url': 'https://lh4.googleusercontent.com/-un6PFw9Mk6Q/AAAAAAAAAAI/AAAAAAAAACA/cwba7Zw9JHI/s128-c0x00000000-cc-rp-mo-ba3/photo.jpg',
                            'rating': 5,
                            'relative_time_description': '3 months ago',
                            'text': 'Old building, but best services',
                            'time': 1521553016
                        },
                        {
                            'author_name': 'Mathews MacLaren',
                            'author_url': 'https://www.google.com/maps/contrib/101744112266500898091/reviews',
                            'language': 'en',
                            'profile_photo_url': 'https://lh3.googleusercontent.com/-slb0zF7N_hw/AAAAAAAAAAI/AAAAAAAAAAA/AB6qoq1MZFsYdi4C7zg2OVrUo4lYtnc6Tw/s128-c0x00000000-cc-rp-mo/photo.jpg',
                            'rating': 1,
                            'relative_time_description': '11 months ago',
                            'text': 'Having to wade through the automated answering service only to be told the wait to speak with a representative will be 30-40 minutes is absurd.  This in itself is extremely poor service.',
                            'time': 1502142984
                        }
                    ],
                'scope': 'GOOGLE',
                'types':
                    [
                        'post_office',
                        'finance',
                        'point_of_interest',
                        'establishment'
                    ],
                'url': 'https://maps.google.com/?cid=5881366581458076327',
                'utc_offset': -420,
                'vicinity': '585 West Line Street, Bishop',
                'website': 'https://tools.usps.com/go/POLocatorDetailsAction!input.action?&radius=20&locationType=po&locationTypeQ=po&locationID=1355026&utm_source=google-my-business-url&utm_medium=search&utm_campaign=yext'
            },
        'status': 'OK'
    }





# gmaps = googlemaps.Client(key='Add Your Key here')
#
# # Geocoding an address
# geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
#
# # Look up an address with reverse geocoding
# reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))
#
# # Request directions via public transit
# now = datetime.now()
# directions_result = gmaps.directions("Sydney Town Hall",
#                                      "Parramatta, NSW",
#                                      mode="transit",
#                                      departure_time=now)


class Navigation(PMainWindow, PtolFace):

    def __init__(self, parent=None):
        super(Navigation, self).__init__(parent)
        PMainWindow.__init__(self)

        self.Ptolemy = parent
        print("Anaximander Parent : ", self.Ptolemy)

        self.setWindowTitle("Anaximander - Ptolemy")

        # TODO:SETTINGS — API key → env var or Kryptos/settings
        self.API_KEY = "AIzaSyCLPZ-AR5SEinJ5GOMFDoWtS3HUu46i68c"
        self.UDP_IP = "192.168.0.7"
        # TODO:SETTINGS — hardcoded port → Tesla/settings tab
        self.UDP_PORT = 5555

        self.gmaps = googlemaps.Client(self.API_KEY)

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.bind((self.UDP_IP, self.UDP_PORT))
        # self.latLong = self.getLocation()
        # self.latLong = (29.967345, -90.031724)
        self.latLong = self.getLocation()
        self.addy = self.gmaps.reverse_geocode(self.latLong)[0]['formatted_address']
        # self.addy = "1317 Lesseps St, New Orleans, LA 70117, USA"
        # print(self.addy)
        self.addyList = self.addy.split(',')
        self.address = str(self.addyList[0]) + "\n" + str(self.addyList[1]) + "\n" + str(self.addyList[2]) + ", " + str(self.addyList[3])
        # print(self.address)

        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        self.homeDir = PTOL_ROOT + "/"
        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        self.imgDir = PTOL_ROOT + "/images/Anaximander/"
        self.styles = "QMainWindow { border: 1px solid white; background-color: black; color: white } " \
                      "QWidget { background-color: black; color: white } " \
                      "QMenuBar { border: 1px solid white; background-color: black; color: white } " \
                      "QMenuBar::item { background-color: black; color: white } " \
                      "QToolBar { border: 1px solid white; background-color: black; color: white } " \
                      "QToolButton { background-color: black; color: white } " \
                      "QToolButton::hover { background-color: blue; color: white } " \
                      "QStatusBar { border: 1px solid white; background-color: black; color: white } " \
                      "QTabWidget { border: 1px solid white; background-color: black; color: white } " \
                      "QTabBar::tab { border: 1px solid white; background-color: black; color: white } " \
                      "QWebView { border: 1px solid white; background-color: white; color: black } " \
                      "QComboBox { border: 1px solid white; background-color: grey; color: black } " \
                      "QComboBox::item { background-color: grey; color: black } " \
                      "QPushButton { border: 1px solid cyan; background-color: cyan; color: black } " \
                      "QFrame {border: 1px solid cyan; background-color: cyan; color: cyan; } " \
                      "QRadioButton { background-color: black; color: white;} " \
                      "QRadioButton::label {align: right} " \
                      "QRadioButton::indicator{ border: 1px solid cyan; border-radius: 6px; color: cyan; background-color: black;} " \
                      "QRadioButton::indicator::checked{ border: 1px solid cyan; border-radius: 6px; color: black; background-color: cyan;} " \
                      "QLineEdit { border: 1px solid white; background-color: grey; color: black } " \
                      "QDockWidget { border: 1px solid white; background-color: black; color: white } " \
                      "QTableWidget { background-color: white; color: black } " \
                      "QTextBrowser { border: 1px solid black; background-color: white; color: black } " \
                      "QLabel {border: 1px solid black; color: black } " \
                      "QListWidget { background-color: grey; color: black } " \
                      "QListWidgetItem { border: 1px solid black } " \
                      "QTableWidget { background-color: black; color: white } " \
                      "QTableWidget::item:focus { border: 1px solid white; background-color: blue; color: white } " \
                      "QHeaderView::section { background-color: darkblue; color: white } QTextEdit { border: 1px solid black; color: black }"
        self.btnSize = 35

        # Modules
        if self.Ptolemy:
            self.dialogs = self.Ptolemy.dialogs
            print(self.dialogs)
            self.database = self.Ptolemy.db
            self.opener = self.Ptolemy.opener
            print("Loaded Ptolemy Modules")

        else:
            from Pharos.Dialogs import Dialogs
            from Callimachus.Database import Database
            self.dialogs = Dialogs(parent=self)
            self.database = Database(parent=self)
            self.opener = build_opener()
            self.opener.addheaders = [("User-agent", "Mozilla/5.0")]
            print("Loaded Anaximander Modules")
        
        print("initUI next")
        self.initUi()

    def initUi(self):

        self.assistant = QWidget(self)
        self.assistant.setStyleSheet(self.styles)
        self.setCentralWidget(self.assistant)

        self.title = str(self.address) + "\n" + str(self.latLong[0]) + " : " + str(self.latLong[1])

        self.location = QLabel(self.title)
        self.location.setStyleSheet(self.styles)
        self.location.setFixedHeight(self.btnSize)
        self.location.setAlignment(Qt.AlignCenter)
        self.location.setFixedHeight(75)

        self.dirBtn = QSvgWidget(self.imgDir + 'setdestination.svg')
        self.dirBtn.setGeometry(0, 0, self.btnSize, self.btnSize)
        self.dirBtn.setStyleSheet(self.styles)
        self.dirBtn.setFixedSize(self.btnSize, self.btnSize)
        self.dirBtn.setToolTip('Find Directions')
        self.dirBtn.mousePressEvent = self.getDirections

        self.searchBtn = QSvgWidget(self.imgDir + "placesnearby.svg")
        self.searchBtn.setGeometry(0, 0, self.btnSize, self.btnSize)
        self.searchBtn.setStyleSheet(self.styles)
        self.searchBtn.setFixedSize(self.btnSize, self.btnSize)
        self.searchBtn.setToolTip('Search Nearby')
        self.searchBtn.mousePressEvent = self.searchNearby

        self.instructions = QListWidget(self)
        self.instructions.setStyleSheet(self.styles)
        self.instructions.setFixedHeight(250)
        self.instructions.currentItemChanged.connect(self.showText)
        self.instructions.itemDoubleClicked.connect(self.directionsToPlace)

        self.text = QTextEdit(self)
        self.text.setStyleSheet(self.styles)
        self.text.setFixedWidth(400)
        self.text.setAlignment(Qt.AlignCenter)
        # self.text.mouseDoubleClickEvent = lambda event, text: self.speakStep(event, self.text.toPlainText())


        self.layout = QGridLayout(self)
        self.layout.addWidget(self.location, 0, 0, 2, 4)
        self.layout.addWidget(self.dirBtn, 2, 0, 1, 1)
        self.layout.addWidget(self.searchBtn, 2, 1, 1, 1)
        self.layout.addWidget(self.instructions, 3, 0, 10, 4)
        self.layout.addWidget(self.text, 0, 5, 13, 5)
        self.assistant.setLayout(self.layout)
        self.assistant.show()


        pass

    def getDirections(self, event, directions=None):
        print("Getting Directions")

        self.entryType = 'directions'
        if directions:
            self.directions = directions
            itemNumber = 1
            self.instructions.clear()
            for step in directions[0]['legs'][0]['steps']:
                stepName = 'Step {0}'.format(str(itemNumber))
                # print("StepName : ", stepName)
                self.listentry(stepName, 'black', 'cyan')
                itemNumber += 1
            pass

        else:

            methods = [0, 'driving', 'walking', 'bicycling', 'transit']
            dataList = [('Start Location', self.addy), ('Destination', '422 Harmony St, New Orleans, LA'), ('Method', methods), ('Departure Time', datetime.now())]
            title = "Get Directions"
            comment = "Input Destination"
            results = fedit(dataList, title, comment)

            if not results:

                pass

            else:

                startLatLong = self.gmaps.geocode(str(results[0]))[0]['geometry']['location']
                start = (startLatLong['lat'], startLatLong['lng'])
                endLatLong = self.gmaps.geocode(str(results[1]))[0]['geometry']['location']
                end = (endLatLong['lat'], endLatLong['lng'])
                method = str(methods[results[2] + 1])
                time = results[3]
                print(start, end, method, time)
                self.directions = self.gmaps.directions(start, end, mode=method, departure_time=time)
                print(self.directions)

                itemNumber = 1
                self.instructions.clear()
                for step in self.directions[0]['legs'][0]['steps']:
                    stepName = 'Step {0}'.format(str(itemNumber))
                    # print("StepName : ", stepName)
                    self.listentry(stepName, 'black', 'cyan')
                    itemNumber += 1

        pass

    def searchNearby(self, event):
        print('Searching Nearby')

        self.entryType = 'nearbyPlaces'

        radii = [0, '5', '10', '15', '20', '25', '30', '35', '40', '45', '50']
        dataList = [("Location", str(self.latLong[0]) + ", " + str(self.latLong[1])), ('Radius', radii), ('Keywords', 'gas station')]
        title = "Fine Nearby Places"
        comment = "Input Location, Radius and Keywords"
        results = fedit(dataList, title, comment)
        print(results)

        if not results:
            pass

        else:
            searchLoc = results[0].split(',')
            searchLocation = (float(searchLoc[0]), float(searchLoc[1]))
            print(searchLocation)
            searchRadius = radii[results[1] + 1]
            print(searchRadius)
            searchKeywords = results[2]
            print(searchKeywords)

            self.nearbyPlaces = self.gmaps.places(location=searchLocation, radius=searchRadius, query=searchKeywords)
            print(self.nearbyPlaces)

            itemNumber = 1
            self.instructions.clear()
            for place in self.nearbyPlaces['results']:
                name = place['name'] + " " + str(itemNumber)
                self.listentry(name, 'black', 'cyan')
                itemNumber += 1


        pass

    def getLocation(self):
        # self.ip = self.getPublicIP()
        self.ip = self.getLocalIP()
        # print(self.ip)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.connect(('80.255.11.139', 32323))
        self.sock.send(b'collect')

        self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock2.bind((self.ip, 5555))
        data = ()
        # print(data)
        # self.dictionary = {}
        while data == ():
            data, addr = self.sock2.recvfrom(1024)
            # print(data)
            self.dictionary = self.dataFix(data)
            # print(self.dictionary)
            self.lat = self.dictionary[b'lat']
            self.lon = self.dictionary[b'lon']
            self.altitude = self.dictionary[b'altitude']

        print("Location Received")
        return (float(self.lat), float(self.lon))


        #
        # while int(latLong[1]) != 1:
        #     data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
        #     latLong = data.split(b',')
        #     if int(latLong[1]) == 1:
        #         print(float(latLong[2]), float(latLong[3]))
        #         location = (float(latLong[2]), float(latLong[3]))
        #         return location



        pass

    def getLocalIP(self, iface='wlp2s0'):#bnep0'):#wlp2s0'):
        process = Popen(
            args="ifconfig -a {0} | grep 'inet '".format(iface),
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0].replace(b"        ", b"").split(b" ")[1]
        pass

    def getPublicIP(self):
        process = Popen(
            args="dig +short myip.opendns.com @resolver1.opendns.com",
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0].replace(b"\n", b"")

    def dataFix(self, data):

        dataList = data[1:-1].split(b', ')
        # print("DATALIST ", dataList)
        dataDict = {}
        for i in dataList:
            i = str(i).split(': ')
            # print("I = ", str(i), str(i[0]).replace("""b\"""", ""))
            # print("NEXT I", str(i[0][1:]).replace("'", ""), str(i[1]))
            dataDict[str(i[0]).replace("""b\"b""", "").replace("'", "").encode()] = str(i[1]).replace("\"", "").encode()

        # print("DATADICT ", dataDict)
        return dataDict

    def listentry(self, text, tcolor='white', bcolor='black'):

        itemIn = QListWidgetItem(text)
        itemIn.setForeground(QColor(tcolor))
        itemIn.setBackground(QColor(bcolor))
        self.instructions.addItem(itemIn)

    def showText(self):
        print(self.instructions.currentItem().text())
        # if self.entryType == 'directions':
        #     self.instructions.itemDoubleClicked.connect(lambda: self.speakStep(self.text.toPlainText()))
        # elif self.entryType == 'nearbyPlaces':
        #     self.instructions.itemDoubleClicked.connect(self.directionsToPlace)

        if self.entryType == 'directions':

            itemIndex = self.instructions.currentItem().text().split(" ")[-1]
            print("ITEMINDEX : ", itemIndex)
            print("ENTRYTYPE : ", self.entryType)
            directionList = self.directions[0]['legs'][0]['steps']
            response = h2t(directionList[int(itemIndex) - 1]['html_instructions']).replace("*", "").replace("\n", " ")
            print("RESPONSE : ", response)

            self.text.setText(response)
            self.speak(response)
            return


        elif self.entryType == 'nearbyPlaces':

            itemIndex = self.instructions.currentItem().text().split(" ")[-1]
            print("Index : " + itemIndex)
            self.nearbyPlacesList = self.nearbyPlaces['results'][int(itemIndex) - 1]
            # print(self.nearbyPlacesList)
            response = self.nearbyPlacesList['name'] + "\n" + self.nearbyPlacesList['formatted_address']
            print(response)
            self.text.setText(response)
            self.speak(response)


        pass

    def directionsToPlace(self):
        print("getting directions to nearby place")

        start = self.latLong
        end = self.nearbyPlacesList['formatted_address']
        method = 'driving'
        time = datetime.now()

        toDirections = self.gmaps.directions(start, end, mode=method, departure_time=time)
        self.getDirections(event=None, directions=toDirections)

        pass

    def speak(self, text, voice='en'):
        print('speakStep')

        # self.setOutput('Text:\n' + text, 'red')
        text = text.replace("\n", " ")
        text = text.replace(" N ", " North ").replace(" S ", " South ").replace(" E ", " East ").replace(" W ", " West ")
        text = text.replace(" St ", " Street ").replace("St,", "Street,")
        text = text.replace(" BUS ", " Business ")

        print(text)
        espeak.set_parameter(espeak.Parameter.Rate, 175)
        espeak.set_parameter(espeak.Parameter.Wordgap, 3)
        espeak.set_parameter(espeak.Parameter.Pitch, 65)
        espeak.set_parameter(espeak.Parameter.Volume, 55)
        # espeak.set_parameter(espeak.Parameter.Capitals, 1)
        # German: 'de', Ancient Greek: 'other/grc', English: 'en'
        espeak.set_voice(voice)
        espeak.synth(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = Navigation()
    w.resize(250, 150)
    w.move(300, 300)
    # w.setWindowTitle('Simple')
    w.show()

    sys.exit(app.exec())