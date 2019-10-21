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
import re
from urlparse import urlparse

import ad_object

propeller_domains = ["onclkds.com", "deloton.com", "go.pushnative.com", "cobalten.com", "go.oclasrv.com",
        "higheurest.com"]
clickadu_domains = ["moradu.com", "aoredi.com", "vebadu.com", "gebadu.com", "aoredi.com",
        "eoredi.com", "xxlargepop.com", "alxsite.com", "tebadu.com", "horedi.com",
        "ioredi.com", "eoredi.com"]

class AdNetworkIdentifier(object):
    def __init__(self, ad_object):
        self.ad_object = ad_object
        self.extract_urls()

    def extract_urls(self,):
        self.urls = [r[0][2] for r in self.ad_object.redirections if r[0][1] == 'URL']
        self.parsed_urls = [urlparse(u) for u in self.urls]

    def is_revenue_hits(self, parsed_url):
        if (parsed_url.path == "/adServe/banners" and 
                parsed_url.query.startswith("tid=")):
            self.ad_net_domain = parsed_url.netloc
            return True
        if (parsed_url.path.startswith("/banners/script/ui_tag_") and 
                parsed_url.path.endswith(".js")):
            self.ad_net_domain = parsed_url.netloc
            return True
        if (parsed_url.path.startswith("/script/rhpop_") and 
                parsed_url.path.endswith(".js")):
            self.ad_net_domain = parsed_url.netloc
            return True
        # print self.urls
        #import ipdb; ipdb.set_trace()
        return False
        
    def is_pop_cash(self, parsed_url):
        pop_cash = parsed_url.netloc.endswith(".popcash.net")
        if pop_cash:
            self.ad_net_domain = parsed_url.netloc
        return pop_cash

    def is_pop_ads(self, parsed_url):
        pop_ads = parsed_url.netloc.endswith(".popads.net")
        if pop_ads:
            self.ad_net_domain = parsed_url.netloc
        return pop_ads


    def is_pop_my_ads(self, parsed_url):
        pop_my_ads = (parsed_url.netloc == "popmyads.com")
        if pop_my_ads:
            self.ad_net_domain = parsed_url.netloc
        return pop_my_ads

    def is_ad_cash(self, parsed_url):
        ad_cash = (parsed_url.path == "/prod/redirect.html" and parsed_url.query)
        if ad_cash:
            self.ad_net_domain = parsed_url.netloc
        return ad_cash

    # http://rzekbhnk.top/c9/05/36/c9053610c01d1356a73f9b4f736adce7.js
    # http://pl14475563.puserving.com/27/a4/3b/27a43b8438454dd86d9518c8a3ddeea7.js
    def is_ad_sterra(self, parsed_url):
        if not (len(parsed_url.path) == 45 and 
                parsed_url.path.endswith('.js') and
                parsed_url.path[3] == '/' and
                parsed_url.path[6] == '/' and
                parsed_url.path[9] == '/'):
            return False
        splits = parsed_url.path.split('/')
        ad_sterra = (len(splits) == 5 and "".join(splits[:4]) == splits[-1][:6])
        if ad_sterra:
            self.ad_net_domain = parsed_url.netloc
        return ad_sterra

    def is_ad_maven(self, parsed_url):
        if not parsed_url.netloc.endswith('.cloudfront.net'):
            return False
        ad_maven = (len(parsed_url.query) == 12 and re.match('[a-z]{5}=[0-9]{6}', parsed_url.query))
        if ad_maven:
            self.ad_net_domain = parsed_url.netloc
        return ad_maven

    def is_hill_top_ads(self, parsed_url):
        if parsed_url.netloc == 'hilltopads.net':
            self.ad_net_domain = parsed_url.netloc
            return True
        hill_top = (parsed_url.path == "/out" and parsed_url.query.startswith('vt='))
        if hill_top:
            self.ad_net_domain = parsed_url.netloc
        return hill_top

    def is_clicksor(self, parsed_url):
        clicksor = parsed_url.netloc.endswith('.clicksor.net')
        if clicksor:
            self.ad_net_domain = parsed_url.netloc
        return clicksor


    def identify_by_url(self, url, p_url):
        if self.is_revenue_hits(p_url):
            return "RevenueHits"
        if self.is_pop_cash(p_url):
            return "PopCash"
        if self.is_ad_cash(p_url):
            return "AdCash"
        if self.is_pop_ads(p_url):
            return "PopAds"
        if self.is_pop_my_ads(p_url):
            return "PopMyAds"
        if self.is_ad_sterra(p_url):
            return "AdSterra"
        if self.is_hill_top_ads(p_url):
            return "HilltopAds"
        if self.is_clicksor(p_url):
            return "Clicksor"
        if self.is_ad_maven(p_url):
            return "AdMaven"
        if p_url.path == '/apu.php':
            if p_url.netloc in propeller_domains:
                self.ad_net_domain = p_url.netloc
                return "Propeller"
            elif p_url.netloc in clickadu_domains:
                self.ad_net_domain = p_url.netloc
                return "Clickadu"
        return ""
    
    def identify(self,):
        ad_network = ""
        for url, p_url in zip(self.urls[::-1], self.parsed_urls[::-1]):
            if not url or not p_url:
                continue
            ad_network = self.identify_by_url(url, p_url)
            if p_url.path == '/apu.php' and p_url.netloc == "go.onclasrv.net":
                print "Interesting URLs:", self.urls[::-1]
                import ipdb; ipdb.set_trace()
            if ad_network:
                break
        return ad_network if ad_network else "Unknown"

# To be called as part of multiprocessing
def identify_ad_network_mp(ad_path, ad_dict, mal_ad_dict, mal_ad_hashes):
    ad_objs = ad_object.parse_ad_objects(ad_path)
    for ad_obj in ad_objs:
        ani = AdNetworkIdentifier(ad_obj)
        an = ani.identify()
        if ad_obj.screenshot_hash in mal_ad_hashes:
            mal_ad_dict[an] = mal_ad_dict[an] + 1
        ad_dict[an] = ad_dict[an] + 1


def identify_ad_network(ad_object):
    ani = AdNetworkIdentifier(ad_object)
    ad_network = ani.identify()
    if ad_network != "Unknown":
        return ad_network, ani.ad_net_domain
    return ad_network, None
    

