from config import *
import urllib2, urllib, os, json, types
from common.print_logging import logging
import time, datetime

def encodeurl(query,doseq=0, safe = ''):
    """Encode a sequence of two-element tuples or dictionary into a URL query string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError, "not a valid non-string sequence or mapping object", tb

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = urllib.quote(str(k),safe)
            v = urllib.quote(str(v).replace('\'','"'), safe)  # add the replace for php can't get the %27 and %22
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = urllib.quote_plus(str(k), safe)
            if isinstance(v, str):
                v = urllib.quote_plus(v, safe)
                l.append(k + '=' + v)
            elif _is_unicode(v):
                # is there a reasonable way to convert to ASCII?
                # encode generates a string, but "replace" or "ignore"
                # lose information and "strict" can raise UnicodeError
                v = urllib.quote_plus(v.encode("utf-8","replace"))
                l.append(k + '=' + v)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    x = len(v)
                    ty = type(v)
                except TypeError:
                    # not a sequence
                    v = urllib.quote(str(v))
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    l.append(k +'=' +str(v).replace('\'','"'))
                    #for elt in v:
                    #    l.append(k + '=' + urllib.quote_plus(str(elt)))
    final_query = '&'.join(l).replace('\\x','%').replace(' ','') # ADDED for DBCS characters.
    return final_query

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

