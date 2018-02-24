# -*- coding: utf-8-*-
from casescript.common_variable import *
import os

vRAServer = 'test.abc.com'
vRealizeURL = {
                  'GETBearerToken': 'https://%s/identity/api/tokens',
                  'VALIDATEBearerToken': "https://%s/identity/api/tokens/%s",
                  'GETProvisionedResources': 'https://%s/catalog-service/api/consumer/resources/',
                  'GETAllSupportedActions': "https://%s/catalog-service/api/consumer/requests/%s/resourceViews",
              }

vRA_username = 'su-auto@test.abc.com'
vRA_password = '*******'
vRA_tenantURLtoken = 'cloud'
vRA_SessionFile = os.path.join(BASE_DIR, 'data', 'VRealize', 'VRAtoken.json')
vRA_SnapshotFile = os.path.join(BASE_DIR, 'data', 'VRealize', 'VRASnapshot.json')
QUERY_INTERVAL = 10
ACTION_TIMEOUT = 60 # total timeout*interval is 10 minutes
vRA_MountPoint = '/mnt/vRA'
vRA_FTP_Server = '10.XXX.XXX.XXX'
vRA_Domain = 'Domain'
vRA_FTP_username = "su-auto"
vRA_FTP_password = '********'
vRA_FTP_Path = '/ISO_For_VCAC/'
MountCDdeviceType = {
                     'Client': 'Client Device',
                     'Host': 'Host Device',
                     'Datastore': 'Datastore ISO File'
                    }
vRA_ISO_Path = '[ISO]/'
GoldenVMName = GoldenVM
GoldenSnapshot = {
                     "classId": "Infrastructure.Compute.Machine.Snapshot",
                     "componentId": "a7f96ca7-fa97-406d-98ee-3c68329ed37e",
                     "id": GoldenVMID,
                     "label": "DDAN-Auto-0003_Golden"
                 }


vRealizeActions = {
                      'RevertSnapshot': 'POST: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.RevertSnapshot}',
                      'RevertSnapshotTemp': 'GET Template: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.RevertSnapshot}',
                      'CreateSnapshotTemp': "GET Template: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.CreateSnapshot}",
                      'CreateSnapshot': "POST: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.CreateSnapshot}",
                      'DeleteSnapshot': "POST: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.DeleteSnapshot}",
                      'DeleteSnapshotTemp': "GET Template: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.virtual.DeleteSnapshot}",
                      'PowerOnTemp': "GET Template: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.machine.PowerOn}",
                      'PowerOn': "POST: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.machine.PowerOn}",
                      'PowerOFFTemp': "GET Template: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.machine.PowerOff}",
                      'PowerOFF': "POST: {com.vmware.csp.component.iaas.proxy.provider@resource.action.name.machine.PowerOff}",
                      'MountCDTemp': "GET Template: Mount CD-ROM",
                      'MountCD': "POST: Mount CD-ROM"
                  }






