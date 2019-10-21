# This is an enhanced version of the JSgraph code as described in the paper:
#  Bo Li, Phani Vadrevu, Kyu Hyung Lee, Roberto Perdisci. 
# "JSgraph: Enabling Reconstruction of Web Attacks via Efficient Tracking of Live In-Browser JavaScript Executions".
#  Network and Distributed System Security Symposium, NDSS 2018

### Branch roberto:
Changes tn Chromium branch-heads/3267 (VERSION to 64.0.3267.2)
Date:   Mon Nov 13 17:39:54 2017


## Code compilation instructions:
Follow the steps from building chromium for [Linux](https://chromium.googlesource.com/chromium/src/+/lkcr/docs/linux_build_instructions.md)  until ‘gclient runhooks’. After running ‘gclient runhooks’ halt any further instructions and follow as below.

*Steps*:

Clone the repo of depot_tool.
        '''
		         git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
                 export PATH="$PATH:/path/to/depot_tools"
        '''

		Get the code:
        '''
		        mkdir ~/chromium && cd ~/chromium
		        fetch --nohooks chromium
		        cd src
		       ./build/install-build-deps.sh
		        gclient runhooks
        '''

Create a directory for JSGraph and check out the code
Steps:
	cd ~
	mkdir JSGraph
	git checkout https://github.com/perdisci/JSCapsule_code.git
	git fetch
            git checkout phani_se_hunter
Now, go back to Chromium directory and do the remaining part. But this time ensure you are checking out release branch with correct branch number
Steps:
	In this example we will be checking out release branch ‘3282’
	cd ~/chromium/src
			git fetch origin refs/branch-heads/3282
			git checkout FETCH_HEAD
Go back to previous JSGraph and copy to local chromium for dependency of building JSGraph into Chromium
 Steps:
cd ~/jsgraph
rsync -avh --dry-run src/ ../chromium/src/
rsync -avh src/ ../chromium/src/

Follow the rest of the steps as mentioned on Chromium for further building of the executable.
Steps:
	gclient sync
gclient runhooks
gn gen out/Default
autoninja -C out/Default chrome
out/Default/chrome (Voila, you have one!!)

