Configuring Ellis with Amazon SES
=================================

Amazon's Simple Email Service is the preferred email solution for
EC2. This article describes how to configure it to work with Ellis.

Sending emails directly out of EC2 instances can be risky because the
IP addresses may be blacklisted. Using SES avoids this, because it
uses Amazon's infrastructure to send the emails, and it actively
manages sent emails to ensure Amazon's addresses don't get blacklisted
and your emails get through. (E.g., they maintain a feedback loop with
major ISPs so they are informed of individual emails that are marked
as spam, and pass that information back to you; they adaptively limit
sending rates and volume; etc).

To set up development access to SES:

 * Verify your addresses ([docs](http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/InitialSetup.EmailVerification.html)):
   - Choose two or more real addresses for testing: an address to use
     as the sender, and some addresses to use as recipients. They must
     be real, and you must have access to them. You will verify these
     shortly. (In production, you don't need to verify recipient
     addresses, but we're using the sandbox so we do.). I'll use
     foo@example.com as an example.
   - *Beware - verified addresses are case-sensitive before the @ sign!*
   - From the AWS Management Console, go to the [SES
     Console](https://console.aws.amazon.com/ses/home?region=us-east-1).
   - Click "Verify a new sender". (You're currently in sandbox mode -
     that's fine.)
   - Click "Verify a new email address". Enter the email address.
   - Check your email account, and click on the link.
   - Refresh the SES console Verified Senders list and the email address will appear. Repeat for any additional addresses you wish to configure.
 * Get your SMTP credentials ([docs](http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/SMTP.Credentials.html)):
    - *These steps require you to be logged in as "admin".*
    - In the SES console, click "SMTP settings".
    - Click "Create My SMTP Credentials".
    - Accept the default IAM username "ses-smtp-user" (if none appears, you don't have sufficient credentials to proceed).
    - Click "Show User SMTP Credentials". *Copy them / download them and save them in a safe place - you can never see them again!*
    - Close the window.
 * Configure Clearwater [as follows](http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/SMTP.html):

        SMTP_SMARTHOST = "email-smtp.us-east-1.amazonaws.com"
        SMTP_PORT = 25
        SMTP_USERNAME = "the SMTP username from the credentials you obtained above"
        SMTP_PASSWORD = "the SMTP password from the credentials you obtained above"
        SMTP_USE_TLS = True
        EMAIL_RECOVERY_SENDER = "one of the email addresses you verified earlier"

    At the time of writing (April 2013), Amazon has a single SMTP
    smarthost (hosted in the US-East-1 region). Whatever region your
    application is in, you should use the smarthost named above.

    The sender must be a verified email address. In development mode, all recipients must also be verified email addresses.

To set up production access to SES:

 * Log onto the AWS management console as admin.
 * Go to SES.
 * Click on "request production access".
 * Fill in the form, and await Amazon's approval.
