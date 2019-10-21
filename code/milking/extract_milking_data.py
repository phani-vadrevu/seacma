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
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects.json"
MILKING_URLS_PATH = "/home/phani/se_hunter_results/milking_urls.json"
import ad_object
import tldextract
import json
ZERO_HASH = "0"*32

# Milking URL is defined as the first URL with a non-ad domain when 
# walking up the redirection chain
def get_milking_url(ad, tld_extractor):
    # print "Ad URL: ", ad.ad_url
    # Some redirections break in the middle with a blank page. 
    # We need to ignore them
    ad_domain = tld_extractor(ad.ad_url).registered_domain
    upstream_domains = set()
    return_set = None
    if ad.screenshot_hash == ZERO_HASH:
        return_set = (ad_domain, None, None)
    for link in ad.redirections[1:]:
        if link[0][1] == "URL":
            redirect_url = link[0][2]
            # print redirect_url
            redirect_domain = tld_extractor(redirect_url).registered_domain
            if redirect_domain != ad_domain:
                if not return_set:
                    return_set = (ad_domain, redirect_url, redirect_domain)
                # If return_set is marked, then all the next ones are upstream URLs
                else:
                    upstream_domains.add(redirect_domain)
    if not return_set:
        return_set = (ad_domain, None, None)
    return return_set + (upstream_domains,) 

def main():
    tld_extractor = tldextract.TLDExtract(suffix_list_urls=None)
    ad_objs = ad_object.parse_ad_objects(CLUSTERED_ADOBJECTS_PATH)
    ad_domains = set()
    image_hashes = set()
    milking_url_domains = set()
    upstream_domains = set()
    milking_urls = []
    for ad in ad_objs:
        ad_domain, milking_url, milking_domain, curr_upstream_domains = get_milking_url(ad, tld_extractor)
        if milking_domain and milking_domain not in milking_url_domains:
            # print "Milking url: ", milking_url
            # import ipdb; ipdb.set_trace()
            milking_url_domains.add(milking_domain)
            milking_urls.append(milking_url)
        image_hashes.add(ad.screenshot_hash)
        ad_domains.add(ad_domain)
        upstream_domains = upstream_domains.union(curr_upstream_domains)
        # home_domain = self.tld_extract(ad).registered_domain
    print len(ad_objs)
    print "# Ad domains: ", len(ad_domains)
    print "# Image hashes: ", len(image_hashes)
    print "# Milking URLS: ", len(milking_urls)
    print "# Upstream domains: ", len(upstream_domains)
    print "# All domains:", len(ad_domains.union(milking_url_domains).union(upstream_domains))
    dump_object = {"ad_domains": list(ad_domains),
                   "image_hashes": list(image_hashes),
                   "milking_urls": milking_urls,
                   "upstream_domains": list(upstream_domains)}
    with open(MILKING_URLS_PATH, "wb") as f:
        dump_str = json.dumps(dump_object)
        f.write(dump_str)
    # print dump_object["upstream_domains"]


if __name__ == "__main__":
    main()
