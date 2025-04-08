import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SNSService:
    """
    Service for sending mobile notifications using Amazon SNS.
    """
    
    def __init__(self):
        """
        Initialize the SNS service.
        """
        # Get AWS credentials from environment variables
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        
        # Check if credentials are available
        if not self.aws_access_key or not self.aws_secret_key:
            logger.warning("AWS credentials not set. SNS service will not work.")
            self.client = None
        else:
            # Initialize SNS client
            self.client = boto3.client(
                'sns',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
        
        # Store registered phone numbers and their ARNs
        self.phone_endpoints: Dict[str, str] = {}
    
    def register_phone_number(self, phone_number: str) -> Optional[str]:
        """
        Register a phone number for SMS notifications.
        
        Args:
            phone_number: The phone number to register (E.164 format)
            
        Returns:
            The endpoint ARN if successful, None otherwise
        """
        if not self.client:
            logger.error("Cannot register phone number: AWS credentials not set")
            return None
        
        # Check if phone number is already registered
        if phone_number in self.phone_endpoints:
            return self.phone_endpoints[phone_number]
        
        try:
            # Create platform endpoint for the phone number
            response = self.client.create_platform_endpoint(
                PlatformApplicationArn=os.environ.get("SNS_PLATFORM_APPLICATION_ARN"),
                Token=phone_number
            )
            
            endpoint_arn = response.get("EndpointArn")
            if endpoint_arn:
                self.phone_endpoints[phone_number] = endpoint_arn
                logger.info(f"Registered phone number: {phone_number}")
                return endpoint_arn
            else:
                logger.error("Failed to get endpoint ARN from SNS response")
                return None
                
        except ClientError as e:
            logger.error(f"Error registering phone number: {str(e)}")
            return None
    
    def send_notification(self, phone_number: str, message: str) -> bool:
        """
        Send an SMS notification to a phone number.
        
        Args:
            phone_number: The phone number to send to (E.164 format)
            message: The message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Cannot send notification: AWS credentials not set")
            return False
        
        try:
            # Send SMS directly
            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'MeetingAI'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            message_id = response.get("MessageId")
            if message_id:
                logger.info(f"Sent notification to {phone_number}, message ID: {message_id}")
                return True
            else:
                logger.error("Failed to get message ID from SNS response")
                return False
                
        except ClientError as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False