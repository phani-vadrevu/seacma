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
input_urls = [
         # u'http://onlinemoviescinema.com/', u'http://1movies.tv/', u'http://www.vmovee.click/',
         # u'https://www.thebalance.com/watch-free-movies-online-1356647',
         # u'http://sockshare.net/cinema-movies.html', u'http://cmovieshd.com/',
         # u'http://vexmovies.com/', u'http://putlocker.kim/', u'http://www.crackle.com/movies',
         # u'https://www.hulu.com/movies', u'http://www.snagfilms.com/categories/',
         # u'https://123movies.video/', u'https://watchonline.tube/',
         # u'https://www.reddit.com/r/fullmoviesonanything/',
         # u'https://www.youtube.com/watch?v=KN3z-IJBGJU', 
         # u'http://cafemovie.me/',
         # u'http://dudmovies.com/', u'https://www.streamdor.com/', u'http://solarmovie.net/',
         # u'https://movie4u.cc/', u'https://www.yidio.com/movies/filter/free',
         # u'https://tubitv.com/', u'https://www.fmovies.io/', 
         # u'http://www.watchfree.to/',
         # u'http://www.hotstar.com/popular-movies/5713/17',
         # u'https://www.cnet.com/how-to/watch-movies-online-for-free/', u'http://1movies.org/',
         # u'http://putlocker.ac/', 
         # u'http://www.mylifetime.com/videos/movies',
         # u'http://www.hdmovieswatch.eu/',
         # u'https://www.lifewire.com/watch-christmas-movies-on-youtube-3486071',
         # u'http://allusefulinfo.com/watch-movies-online-free-without-registration/',
         # u'http://www.viewster.com/',
         # u'https://www.microsoft.com/en-us/store/p/free-movies-watch-movies-online/9nl64nfk0099',
         # u'http://moviesfoundonline.com/free-movies/', u'https://yesmovies.to/',
         # u'http://123freemovies.net/',
         # u'http://westernsontheweb.com/watch-free-western-movies-online/',
         # u'http://fmovies.org/', u'http://www.openculture.com/freemoviesonline',
         # u'http://blog.buttermouth.com/2007/06/top-25-places-to-watch-free-movies-and.html',
         # u'http://www.boxtv.com/movies/free-movies',
         # u'https://www.allstreamingsites.com/free-movie-streaming-sites-free-movies-online/',
         # u'http://www.hallmarkchanneleverywhere.com/Movies',
         u'https://123movies.co/',
         # u'https://www.dramafever.com/',
         # u'http://alexandrie-montreal.com/2014/03/04/hello-world/',
         # u'https://www.pinterest.com/pin/525302744023610890/',
         u'https://www.isansar.com/movies/hindi-movies/', u'https://megamovies.cc/',
         # u'https://www.ovguide.com/browse_movies?po=free',
         # u'https://www.infogeekers.com/best-free-online-movie-streaming-sites/',
         u'http://losmovies.cc/',
         # u'https://chrome.google.com/webstore/detail/ovoo-watch-free-movies-on/mahfamaaplnjahdkglkfeeaojkmgooll?hl=en-US',
         # u'https://moviesites.me/', u'http://123netflix.com/',
         u'https://www.freemoviescinema.com/',
         # u'https://www.bradsdeals.com/blog/where-to-watch-movies-online-for-free',
         u'http://movies123.in/',
         # u'https://www.quora.com/What-are-the-best-sites-to-watch-Bollywood-movies-for-free',
         # u'http://www.wikihow.com/Watch-Movies-and-TV-Online-for-Free',
         # u'https://www.netflix.com/', u'http://topdocumentaryfilms.com/',
         u'https://movies4u.pro/'
]

# TO DEBUG LATER
# u'https://www.reddit.com/r/fullmoviesonanything/',
# u'http://cafemovie.me/'  .... try to get to ads for this, (may be increase MAX_ELEMENTS_CLICK?)
# u'http://www.mylifetime.com/videos/movies',
# u'http://allusefulinfo.com/watch-movies-online-free-without-registration/',
