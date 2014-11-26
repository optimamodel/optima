#!/bin/bash

#TODO: Set region from one of these keys: http://docs.aws.amazon.com/general/latest/gr/rande.html#elasticbeanstalk_region
EB_REGION=${AWS_DEFAULT_REGION}

# Application name
EB_APP_NAME="optima"

# Environment Tier
EB_ENVIRONMENT_TIER="worker"

# Solution Stack
EB_SOLUTION_STACK="64bit Amazon Linux 2014.03 v1.0.9 running Python 2.7"

# Name of SSH Key
EB_KEY_NAME="Optima"

# Instance type
EB_INSTANCE_TYPE="t1.micro"

# Platform
EB_PLATFORM="Python 2.7"
	
if [ "${1}" = "--init" ]; then
		
	if [ -n "${EB_REGION}" ]; then
		echo "Setup EB application"
		eb init ${EB_APP_NAME} --region ${EB_REGION} --platform "${EB_PLATFORM}" --keyname ${EB_KEY_NAME}
			
	else
		echo "Set EB_REGION to the region to be used"
	fi
		
elif [ "${1}" = "--create" ]; then
	echo "Create EB environment"
	eb create ${EB_APP_NAME}-env --tier ${EB_ENVIRONMENT_TIER} --instance_type ${EB_INSTANCE_TYPE} --platform "${EB_PLATFORM}" --keyname ${EB_KEY_NAME}
	
elif [ "${1}" = "--terminate" ]; then
	echo "Terminate EB environment"
	eb terminate ${EB_APP_NAME}-env --force
	
elif [ "${1}" = "--deploy" ]; then
	echo "Deploy EB application"
	eb deploy

else
	echo "--init    	Setup application"
	echo "--create  	Create environment"
	echo "--terminate   Terminate environment"
	echo "--deploy   	Depploy latest code on branch"
fi

