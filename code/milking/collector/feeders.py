#! /usr/bin/python
###########################################################################
# Copyright (C) 2018 Phani Vadrevu                                        #
# phani@cs.uno.edu                                                        #
#                                                                         #
# Distributed under the GNU Public License                                #
# http://www.gnu.org/licenses/gpl.txt                                     #
#                                                                         #
# This program is free software; you can redistribute it and/or modify    #
# it under the terms of the GNU General Public License as published by    #
# the Free Software Foundation; either version 2 of the License, or       #
# (at your option) any later version.                                     #
#                                                                         #
###########################################################################
from parsers import *

feeders = [
    {
        "URL":
        'http://www.muffleo.site/d24de76e-5155-47ae-8cc4-15e6937e4493?siteID=75294251&imp_id=4o4YsqBoKa9nXgmWjuYKc6YFX6ED9WA3HCNQVeIuSOLDnFJI0KEerncn4y0_rXbfk4Ph4B7qfGWEByswC1ZjzDI_JRWzcsGlXc_H2Ng8iGnw2rIzrqZo5k262LrfHxRUTg05IBN5MvazDkkDeFgp6qOKE0Kn4tPP46UCZQHG2bXNqtnBnoSMdcUN6Av18rdZFgfL29z7d1Lf-RS0n6m6_fq8AjwAt6JVU5t2XG8-2spG4nc3snYy_Mh9V7LiSdcvsVc9hqvHX-Y3_ZnpzEuhMZf7GFa42HAdpD0BBKX0IfqGk2exAGu1A8fV0-_K5vncE0Z7LuEmT1xfK3LeLBC6lBw5kJ910ni8GtIgXjV4K9nYmCmSqrjAYoesl4NLrV8FXHcNXPpG2hCwXh0tUVBCDlsduU1fGOcIFRVnPK6Xn8Ca-CgjMx36IqceC7yaF0KnJtRRSs5c7WXPqRNUZQGpMQF8vaXTuhYSyIS4XrF6gX1d4_Lcj9ci3KP9KhCUs2c2MMbebisLoMahtS-CnKAaFo5PquI4VCe3xrFwZ-wiPaaHJBZQhKneUNVU8E7_EDXK5qItyr9WegIK6OR3jesUY_xDrtZlPg8I048-OePED6sjEmm6NlgBlo2lxoWr02kIqJOZ2VYhaHSXAA',
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 900,
        "Allow-Redirects": True,
        "Parser": multiple_nojs_redirects,
        "Campaign": "java_update_dowloadious_ff_win"

    },
    
    {
        "URL": 'http://marmrtr115.com/idr?srn=sc_marmar2_java&utm_source=sc_marmar2&utm_campaign=d24de76e-5155-47ae-8cc4-15e6937e4493&clickid=wLTRAEGEH67BL0I8H5P0R644',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Frequency": 900,
        "Allow-Redirects": True,
        "Parser": multiple_nojs_redirects,
        "Campaign": "hdplayer_update_dowloadious_safari"

    },
    {
        "URL": "http://server2.rogerclickstrackingtoday.com/?a=AZ&pagex=13&s1=Ozc98oWdwbrdmbvf4YenK0PXi4pJGJvWcfG7veHxBj12m7uKvnt-hIAo-kjoldQAZXXWcl3fno3e1Ilf3jvRiA%2C%2C&os=Windows&browser=Firefox&isp=Charter%20Communications&ip=155.186.190.119",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 300,
        "Allow-Redirects": False,
        "Parser": meta_refresh,
        "Campaign": "tech_support_ff"

    },
    {
        "URL": "http://server1.trckrwrkgud.com/?a=AZ&pagex=0&s1=oxgh7xP6HA0VqrIuuN47y4JQU1IIlRbfyKk42mNDJ_OpbYrPb7--hcc-e-XQZ-HBXPTWhwzit8ZkIK688fQjzQ%2C%2C&os=Windows&browser=Firefox&isp=Charter%20Communications&ip=155.186.190.119",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 600,
        "Allow-Redirects": False,
        "Parser": meta_refresh,
        "Campaign": "tech_support_ff_3"

    },


    #IP for below campaign 212.129.51.188
    {
        "URL": "http://www.yourreliablupgrades.bid/?pcl=ikX6_ufN0mBh71MHbHMd3dCugAKwQTnBqftQw17olPU.&cid=-578143328441389597&sub=661410",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 60,
        "Allow-Redirects": False,
        "Parser": redirect,
        "Campaign": "flash_portalsoft_ff"
    },
    {
            "URL": "http://www.thesoftwareround4updating.stream/?pcl=KDznZjmjF4BXrkGMGXUOPXlcLX2Q8LSP1HsTkCmHMK4.&cid=648a7c3ee5ff2c114801c5751378c1b85cc7b3a1&sid=75548188",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 60,
        "Allow-Redirects": False,
        "Parser": redirect,
        "Campaign": "flash_portalsoft_ff_2"
    },
    {
            "URL": "http://www.thebigandsaferound4updates.trade/?pcl=I6parQdoVZVenHOmsp1Xol1PaZ_Q1W1pvkC0R3Az9oA.&cid=380096669908&sid=1008077",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 60,
        "Allow-Redirects": False,
        "Parser": redirect,
        "Campaign": "flash_portalsoft_ff_3"
    },
    {
        "URL":
        'http://tr3str.com/irtr?id=1202&clickid=adkm_h9agJTrECoS_ncWYWfIzag_f345YONMKYftr0ox8kzKd9yg1pf1BcaRRpjFo-9KhB_DFLsvV_X7mmhtHZbVcTdrJSNN06j5gJL8UE7ku6C7aiSZhPqoHFi5jBAxJEWNBJmC1ugO8QxSGTY0BpBo0R8BqFp6Guzdjg50Ez8uWNbcCRE9evi8SXaOFWHjk0ExZ7c5eZyQ3ehjVb5qRGQFUmaeejCaGyf46PObDL60OawP4dNzltKhTklIm1YcjBy9vpGm3-VottmsZtlgHpZYW2DhL1HpUqf5sd2F8vwTDmVGs-lAKocIzj3DkUJ50rFk2_XrSet0U89-9JltIxejvC42E1sZ-2BhFWMo-pd1VNL8kQGQ5hHLjsriifCcSfkM_Rth5wGneNjEwqzCPugGcs90NpOwdJHUHvpIwMvmoi90wobK7mTct-hwpLqvfcyxjzDy3D7B5sPkTO9bQEYJDz_qKvu4Haj-bakfybm8eLR5CfYi0JOPiN9SsjV4jwzYaU0BOZnWjnXYOfzLtUMROv3Warmk6hEeoizlorcwoCCPrX9BCGtU_mxLe6DO4ZnCZnO7gR1N_Ht3sUcB5zo2JdjKr8VMFYgVpDY8ykSwpkoQ8_ThJ66mvfTHE0X-9m9Uy2QtIKM2TYiO7&utm_content=75548188',
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Frequency": 900,
        "Allow-Redirects": True,
        "Parser": multiple_nojs_redirects,
        "Campaign": "java_update_dowloadious_ff_win_2"

    },

    {
        "URL": 'http://tr3str.com/irtr?id=1202&clickid=adkm_h9agJTrECoS_ncWYWfIzag_f345YONMKYftr0ox8kzKd9yg1pf1BcaRRpjFo-9KhB_DFLsvV_X7mmhtHZbVcTdrJSNN06j5gJL8UE7ku6C7aiSZhPqoHFi5jBAxJEWNBJmC1ugO8QxSGTY0BpBo0R8BqFp6Guzdjg50Ez8uWNbcCRE9evi8SXaOFWHjk0ExZ7c5eZyQ3ehjVb5qRGQFUmaeejCaGyf46PObDL60OawP4dNzltKhTklIm1YcjBy9vpGm3-VottmsZtlgHpZYW2DhL1HpUqf5sd2F8vwTDmVGs-lAKocIzj3DkUJ50rFk2_XrSet0U89-9JltIxejvC42E1sZ-2BhFWMo-pd1VNL8kQGQ5hHLjsriifCcSfkM_Rth5wGneNjEwqzCPugGcs90NpOwdJHUHvpIwMvmoi90wobK7mTct-hwpLqvfcyxjzDy3D7B5sPkTO9bQEYJDz_qKvu4Haj-bakfybm8eLR5CfYi0JOPiN9SsjV4jwzYaU0BOZnWjnXYOfzLtUMROv3Warmk6hEeoizlorcwoCCPrX9BCGtU_mxLe6DO4ZnCZnO7gR1N_Ht3sUcB5zo2JdjKr8VMFYgVpDY8ykSwpkoQ8_ThJ66mvfTHE0X-9m9Uy2QtIKM2TYiO7&utm_content=75548188',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Frequency": 900,
        "Allow-Redirects": True,
        "Parser": multiple_nojs_redirects,
        "Campaign": "hdplayer_update_dowloadious_safari_2"

    },
]
    #Retired Stuff
    #{
        #"URL": "https://seedwell.info/video/",
        #"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        #"Frequency": 1800,
        #"Allow-Redirects": False,
        #"Parser": redirect,
        #"Campaign": "tech_support_ff_2"
    #},
    #IP for below campaign 212.129.49.120
    #{
        #"URL": "http://www.worldwide2upgrading.download/?pcl=KDznZjmjF4BXrkGMGXUOPXlcLX2Q8LSP1HsTkCmHMK4.&cid=e55253b2f66b061a35a6e7a375a133091d2b630b&sid=75548188",
        #"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        #"Frequency": 60,
        #"Allow-Redirects": False,
        #"Parser": redirect,
        #"Campaign": "flash_portalsoft_ff_3"
    #},
    #{
        #"URL": "http://www.videosearchingspacetoupdating.bid/NQEwoTkUFWURlDT-uJ2rcXlrd-U_I9wTUS0hQkNIE7Y./?&cid=15061062462612706935176263052872745&SUB_ID=1622809",
        #"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        #"Frequency": 60,
        #"Allow-Redirects": False,
        #"Parser": redirect,
        #"Campaign": "flash_testingwarehouse_ff"
    #}

    # The URL is marked my GSB
    #IP for below campaign 212.129.53.8
    #{
        #"URL": "http://www.thebigandalwaysforupgrade.club/?pcl=8tdz6K24IwdZ3JqWc_SzMeYPd69l5nprPWBp0bTR6iU.&cid=15073156790855172843172531727255633&SUB_ID=354662",
        #"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        #"Frequency": 60,
        #"Allow-Redirects": False,
        #"Parser": redirect,
        #"Campaign": "flash_portalsoft_ff_4"
    #},
