#!/bin/bash

#TODO: Set to location of eb tools downloaded from here: http://aws.amazon.com/code/6752709412171743
EB_PATH=""

#TODO: Set AWS access key. Can be generated by following instructions under Access keys:
# http://docs.aws.amazon.com/general/latest/gr/getting-aws-sec-creds.html
EB_ACCESS_KEY_ID=""
EB_SECRET_ACCESS_KEY=""

#TODO: Set region from one of these keys: http://docs.aws.amazon.com/general/latest/gr/rande.html#elasticbeanstalk_region
EB_REGION="us-east-1"

# Application name
EB_APP_NAME="optima"

# Environment Tier
EB_ENVIRONMENT_TIER="WebServer::Standard::1.0"

# Solution Stack
EB_SOLUTION_STACK="64bit Amazon Linux 2014.03 v1.0.9 running Python 2.7"

if [ -n "${EB_PATH}" ]; then
	
	if [ "${1}" = "--setup" ]; then
		
		if [ -n "${EB_ACCESS_KEY_ID}" ] && [ -n "${EB_SECRET_ACCESS_KEY}" ] && [ -n "${EB_REGION}" ]; then
			echo "Setup EB application"
			${EB_PATH}/eb init -I ${EB_ACCESS_KEY_ID} -S ${EB_SECRET_ACCESS_KEY} --region ${EB_REGION} -a ${EB_APP_NAME} -e ${EB_APP_NAME}-env -t "${EB_ENVIRONMENT_TIER}" -s "${EB_SOLUTION_STACK}"
		
			echo "Configuring git"
			${EB_PATH}/../../../AWSDevTools/Linux/AWSDevTools-RepositorySetup.sh
			git aws.config
			
		else
			echo "Set the EB_ACCESS_KEY_ID and EB_SECRET_ACCESS_KEY to your AWS access key credentials. Also set EB_REGION to the region to be used"
		fi
		
	elif [ "${1}" = "--start" ]; then
		echo "Run EB application"
		${EB_PATH}/eb start
	elif [ "${1}" = "--stop" ]; then
		echo "Stop EB application"
		${EB_PATH}/eb stop
	elif [ "${1}" = "--delete" ]; then
		echo "Delete EB application"
		${EB_PATH}/eb delete
	else
		echo "--setup    Setup application"
		echo "--start    Start application"
		echo "--stop     Stop application"
		echo "--delete   Delete application"
	fi
	
else
    echo "Set the EB_PATH to location of AWS Elastic Beanstalk Command Line Tools. Can be downloaded from here: http://aws.amazon.com/code/6752709412171743"
fi
