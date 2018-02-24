from config import *
import urllib2, urllib, os, json, types
from common.print_logging import logging
import time, datetime
from common.DDAN_UI_Option import encodeurl

class VRealizeObject():
    def __init__(self, vRADomain = vRAServer):
        self.vRADomain = vRADomain
        self.vRAToken = None
        # Read the session info from file first
        # if the token expires or the error when load the file
        # we get the token again
        try:
            tmp_sessionfile = open(vRA_SessionFile, 'r')
            res = tmp_sessionfile.readlines()
            tmp_sessionfile.close()
            res = json.loads(res[0])
            self.read_token(res)
            if datetime.datetime.utcnow().isoformat() > self.time_expire:
                logging.error('token has timeout now try to request a new token')
                self.vRAToken = None
        except Exception as e:
            logging.error(e)
            self.vRAToken = None
        if self.vRAToken == None:
            try:
                self.get_VRA_token()
            except Exception as e:
                logging.error(e)

    def get_VRA_token(self):
        '''
        Purpose:
            update the token files
        '''
        TokenURL = vRealizeURL['GETBearerToken']%self.vRADomain
        data = {"username":vRA_username, "password": vRA_password, "tenant": vRA_tenantURLtoken}
        code, res = self.post_data(TokenURL, data)
        if code <> 200:
            logging.error("get VRealize token error")
            raise Exception('Get VRealize token error')
        res = json.loads(res)
        self.read_token(res)
        if  self.validate_VRA_token() == False:
            logging.error("validate VRealize token error")
            raise Exception('Validate VRealize token error')
        with open(vRA_SessionFile, 'w') as outfile:
            json.dump(res, outfile)

    def validate_VRA_token(self):
        '''
        Purpose:
            validate the token is correct
        '''
        if self.vRAToken == None:
            return False
        ValidateURL = vRealizeURL['VALIDATEBearerToken']%(self.vRADomain, self.vRAToken)
        code, res = self.get_data(ValidateURL, method = 'HEAD')
        if code<>204:
            logging.error('validate VRealize token error')
            return False
        return True


    def read_token(self, res_json):
        self.time_expire = res_json['expires']
        self.vRAToken = res_json['id']
        self.vRAtenant = res_json['tenant']

    def post_data(self, url, data):
        """
        Parameters:
           url: URL to launch
           data: string/tuple/dictionary
        Return:
            the response object if no error occure, any error will cause Exception
        """
        opener = urllib2.Request(url, json.dumps(data), headers={'Content-type': 'application/json', 'Accept': 'application/json'})
        if self.vRAToken != None:
            if datetime.datetime.utcnow().isoformat() > self.time_expire:
                logging.error('token has timeout now try to request a new token')
                self.get_VRA_token()
            opener.add_header('Authorization', 'Bearer '+str(self.vRAToken))
        """
        if type(data) is types.DictionaryType or type(data) is types.TupleType:
            data = urllib.urlencode(data)
            #data = encodeurl(data, doseq=doseq, safe='\\x')
        """

        logging.debug('in VRealizeObject.post data, parameter: url=%s, data=%s' % (url, str(data)))
        try:
            response = urllib2.urlopen(opener)
        except urllib2.HTTPError, e:
            logging.error(e)
            return e.code, e.reason
        code=response.getcode()
        try:
            ResponseStr = response.read()
            if len(ResponseStr)>300:
                logging.debug("response str is %s" % ResponseStr[:300])
            else:
                logging.debug("response str is %s" % ResponseStr)
        except:
            ResponseStr = ''
        response.close()
        return code, ResponseStr
       

    def get_data(self, url, data={}, method=None):
        """
        Used get method to access web application and get the response.

        :Parameters:
            uri: string
                 The URI to launch.
        :Return:
        The return code and content
        exception.
        """
        if data <> {}:
            data = encodeurl(data)
            url +='?'+data

        logging.info("in VRealizeObject.get_data, parameter: url="+ url)

        opener = urllib2.Request(url, None, headers={"Cache-Control":"no-cache", 'Accept': 'application/json'})
        if self.vRAToken != None:
            if datetime.datetime.utcnow().isoformat() > self.time_expire:
                logging.error('token has timeout now try to request a new token')
                self.get_VRA_token()
            opener.add_header('Authorization', 'Bearer '+str(self.vRAToken))
            #opener.addheaders = [('Authorization', 'Bearer %s'%self.vRAToken)]

        if method != None:
            opener.get_method = lambda : method
        try:
            response = urllib2.urlopen(opener)
        except urllib2.HTTPError, e:
            logging.error(e)
            return e.code, e.reason
        code = response.getcode()
        logging.debug(code)
        try:
            ResponseStr = response.read()
            if len(ResponseStr)>300:
                logging.debug("response str is %s " % ResponseStr[:300])
            else:
                logging.debug("response str is %s" % ResponseStr)
        except:
            ResponseStr = ''
        response.close()

        return code, ResponseStr 

if __name__ == "__main__":
    ui = VRealizeObject()

