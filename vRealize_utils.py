from vRealize import *
from casescript.install.mk_iso import FTPconnector
from casescript.install.install_variable import ISO_LOCATION
import ftplib
import os

def get_vRealize_Machine_ReqID(MachineName, vRA=None):
    '''
    Purpose:
       The vRealize automation actions are based on the Machine RequestID, we need to get it by name first.
    Input:
        Machine Name
    Output:
        Request ID 
        None if can not find it
    '''
    if vRA==None:
        vRA = VRealizeObject();

    # while loop until get the ecpected MachineName in return json
    # Or exit the loop when content is empty
    page = 1
    while True:
        ResourceURL = vRealizeURL['GETProvisionedResources']%vRA.vRADomain
        data = {"page": page}
        code, res = vRA.get_data(ResourceURL, data)
        if code <> 200:
            logging.error("get resource fail for return code %d" % int(code))
            return None
        res = json.loads(res)
        logging.debug('Now get the return resource info in page %d, info %s' % (page, str(res)))
        if res['content'] == []:
            logging.info('Failed to find the device %s in all page' % (MachineName))
            return None
        for item in res['content']:
            if item['name'] == MachineName:
                logging.debug('Found the device %s, resource info: %s' % (MachineName, str(item)))
                return item['requestId']
        logging.info('Failed to find the device %s in page %d' % (MachineName, page))
        page = page +1;

def get_vRealize_Machine_Actions(requestID, action=None, vRA=None):
    '''
    Purpose:
        get the request url based on the request ID(machine identification)
    Input:
        requestID: point to a machine
        action: return the currspond action url and send method, default is None, return all the supported actions
    return:
        json formate output with url, action template and the send method
    '''
    if vRA==None:
        vRA = VRealizeObject();
    ResourceURL = vRealizeURL['GETAllSupportedActions']%(vRA.vRADomain, requestID)
    code, res = vRA.get_data(ResourceURL)
    if code<>200:
        logging.error("get resource fail for return code %d" % int(code))
        return None
    res = json.loads(res)
    if action == None:
        logging.debug('get supported action list success: %s'%str(res))
        return res
    try:
        for item in res['content']:
             for link in item["links"]:
                if action in link["rel"]:
                    # when find the matched item, return the link directly
                    logging.debug('get supported %s success: %s'%(action, str(action)))
                    return link['href']
        return None 
    except Exception as e:
        logging.error(e)
        return None

def check_machine_status(requestID, vRA=None):
    '''
    Get the requestID machine status
    '''
    status = None
    machine_info = get_vRealize_Machine_Actions(requestID, vRA=vRA)
    try:
        for item in machine_info["content"]:
            # only the vm status in the section with name
            if item["status"] in ['On', 'Off']:
                return item["status"]
    except Exception as e:
        logging.error(e)
    return None

def check_action_finished(requestID, action, vRA=None):
    '''
    Purpose:
       check an action is finished on Vrealize
    Input:
        requestID, specify the virtual machine in vRealize
        action, the action is performed
        vRA, the vrealize object
    Output:
        True: the action is finished
        False: timeout reached but still not success
    '''
    # When doing this action the vrealize resouce will not return the snapshot related urls any more,
    # we can use this to validate if the revert snapshot is successful
    for i in range(ACTION_TIMEOUT):
        time.sleep(QUERY_INTERVAL)
        return_url = get_vRealize_Machine_Actions(requestID, action=action, vRA=vRA)
        if return_url != None:
            break
    if return_url == None:
        return False
    else:
        return True

def get_latest_vRealize_Snapshot(requestID, vRA=None):
    '''
    Purpose:
        Currently, we can not get the snapshot reference by the Restful API privided by vRealize Automation
        So we use the advantage of get revert template, which will return the latest snapshot info
    Return:
        the SnapshotReference information
        None if fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    # get vRealize Template first
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['RevertSnapshotTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize revert action template url fail')
        return None
    logging.debug('Get vrealize revert template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize revert template fail.")
        return None
    template = json.loads(res)
    logging.debug('get revert template success %s' % str(template))
    return template['data']['SnapshotReference']

def revert_vRealize_Snapshot(requestID, SnapshotReference, vRA=None):
    '''
    Purpose
        revert a machine in vRealize
    Input
        requestID, specify the virtual machine in vRealize
        SnapshotReference, {
            "classId": "Infrastructure.Compute.Machine.Snapshot",  (fixed)
            "componentId": "a7f96ca7-fa97-406d-98ee-3c68329ed37e", (the id of snapshot)
            "id": "426",                                           (another id)
            "label": "Installed"                                   (Name when create the snapshot)
        }
        
    Output
        True: Success
        False: Fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    # get vRealize Template first
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['RevertSnapshotTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize revert action template url fail')
        return False
    logging.debug('Get vrealize revert template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize revert template fail.")
        return False
    template = json.loads(res)
    logging.debug('get revert template success %s' % str(template))
    # post the vRealize snapshot template
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['RevertSnapshot'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize revert action url fail')
        return False
    logging.debug('Get vrealize revert url success: %s' % action_url)
    template['data']['SnapshotReference']=SnapshotReference
    code, res = vRA.post_data(action_url, template)
    if code <> 201:
        logging.error("revert snapshot fail %d, error: %s" % (code, str(res)))
        return False
    if check_action_finished(requestID, vRealizeActions['RevertSnapshotTemp'], vRA):
        logging.debug("revert snapshot success")
        return True
    else:
        logging.error("revert snapshot fail")
        return False

def create_vRealize_Snapshot(requestID, snapshot_name, description='', enable_memory=False, vRA=None):
    '''
    Purpose:
        Create a snapshot on the specific machine
    Input:
        requestID:  UUID to indentify the virtual machine
        snapshot_name: the name to create the snapshot
        description: snapshot description
        enable_memory: snapshot memory as well? default No, CURRENT we can not create the ram enabled snapshot
        vRA: the object the communicating with vrealize API
    output:
        True: Success
        False: Fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    # We need to ensure the machine is on when enable memory is True
    if enable_memory:
        status = check_machine_status(requestID, vRA)
        if status == 'On':
            pass
        else:
            logging.error('Can not create snapshot with memory when machine is %s' % str(status))
            return False

        
    # get vRealize Template first
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['CreateSnapshotTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize create snapshot action template url fail')
        return False
    logging.debug('Get vrealize create template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get create revert template fail.")
        return False
    template = json.loads(res)
    logging.debug('get create template success %s' % str(template))
    # post the vRealize snapshot template
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['CreateSnapshot'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize create action url fail')
        return False
    logging.debug('Get vrealize create url success: %s' % action_url)
    template['data']["provider-SnapshotInputDescription"] = description
    template['data']["provider-SnapshotInputMemoryIncluded"] = enable_memory
    template['data']["provider-SnapshotInputName"] = snapshot_name
    code, res = vRA.post_data(action_url, template)
    if code <> 201:
        logging.error("Create snapshot fail %d, error: %s" % (code, str(res)))
        return False
    if check_action_finished(requestID, vRealizeActions['CreateSnapshotTemp'], vRA):
        logging.debug("Create snapshot success")
        return True
    else:
        logging.error("Create snapshot fail")
        return False

def delete_vRealize_Snapshot(requestID, SnapshotReference, vRA=None):
    '''
    Purpose
        delete a snapshot in vRealize
    Input
        requestID, specify the virtual machine in vRealize
        SnapshotReference, {
            "classId": "Infrastructure.Compute.Machine.Snapshot",  (fixed)
            "componentId": "a7f96ca7-fa97-406d-98ee-3c68329ed37e", (the id of snapshot)
            "id": "426",                                           (another id)
            "label": "Installed"                                   (Name when create the snapshot)
        }
        
    Output
        True: Success
        False: Fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    # get vRealize Template first
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['DeleteSnapshotTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize delete action template url fail')
        return False
    logging.debug('Get vrealize delete template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize delete template fail.")
        return False
    template = json.loads(res)
    logging.debug('get delete template success %s' % str(template))
    # post the vRealize snapshot template
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['DeleteSnapshot'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize Delete action url fail')
        return False
    logging.debug('Get vrealize delete url success: %s' % action_url)
    template['data']['SnapshotReference']=SnapshotReference
    code, res = vRA.post_data(action_url, template)
    if code <> 201:
        logging.error("delete snapshot fail %d, error: %s" % (code, str(res)))
        return False
    if check_action_finished(requestID, vRealizeActions['DeleteSnapshotTemp'], vRA):
        logging.debug("Delete snapshot success")
        return True
    else:
        logging.error("Delete snapshot fail")
        return False

def power_off_vRealize_Machine(requestID, vRA=None):
    '''
    Purpose
        Poweroff a snapshot in vRealize
    Parameter
        requestID, specify the virtual machine in vRealize
        vRA, the vrealize object
    Output:
        True: Success
        False: Fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    status = check_machine_status(requestID, vRA)
    if status == 'Off':
        logging.debug("System already OFF")
        return True
    else:
        logging.error('System status is %s' % str(status))
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['PowerOFFTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize poweroff action template url fail')
        return False
    logging.debug('Get vrealize poweroff template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize poweroff template fail.")
        return False
    template = json.loads(res)
    logging.debug('get poweroff template success %s' % str(template))
    # post the vRealize snapshot template
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['PowerOFF'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize poweroff action url fail')
        return False
    logging.debug('Get vrealize poweroff url success: %s' % action_url)
    code, res = vRA.post_data(action_url, template)
    if code <> 201:
        logging.error("Power off fail %d, error: %s" % (code, str(res)))
        return False
    if check_action_finished(requestID, vRealizeActions['PowerOFFTemp'], vRA):
        logging.debug("Power Off success")
        return True
    else:
        logging.error("Power Off fail")
        return False

def power_on_vRealize_Machine(requestID, vRA=None):
    '''
    Purpose
        Poweron a snapshot in vRealize
    Parameter
        requestID, specify the virtual machine in vRealize
        vRA, the vrealize object
    Output:
        True: Success
        False: Fail
    '''
    if vRA==None:
        vRA = VRealizeObject();
    status = check_machine_status(requestID, vRA)
    if status == 'On':
        logging.debug("System already ON")
        return True
    else:
        logging.error('System status is %s' % str(status))
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['PowerOnTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize poweron action template url fail')
        return False
    logging.debug('Get vrealize poweron template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize poweron template fail.")
        return False
    template = json.loads(res)
    logging.debug('get poweron template success %s' % str(template))
    # post the vRealize template
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['PowerOn'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize poweron action url fail')
        return False
    logging.debug('Get vrealize poweron url success: %s' % action_url)
    code, res = vRA.post_data(action_url, template)
    if code <> 201:
        logging.error("Power on fail %d, error: %s" % (code, str(res)))
        return False
    if check_action_finished(requestID, vRealizeActions['PowerOnTemp'], vRA):
        logging.debug("Power On success")
        return True
    else:
        logging.error("Power On fail")
        return False

def MountCD_vRealize_Machine(requestID, deviceType, filePath, connectAtPowerOn=True, vRA=None):
    '''
    Purpose:
        configure the vrealize machine to mount a specific IP address
    Parameter:
        requestID, specify the virtual machine in vRealize
        vRA, the vrealize object
        deviveType, Client/Host/Datastore
        filePath, relevant file path to the vRA_FTP_Path
    '''
    if deviceType not in MountCDdeviceType:
        logging.error("Device type error should be one of Client/Host/Datastore")
        return False
    if vRA==None:
        vRA = VRealizeObject()
    template_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['MountCDTemp'], vRA=vRA)
    if template_url == None:
        logging.error('Get vrealize mount cd action template url fail')
        return False
    logging.debug('Get vrealize mount cd template url success: %s' % template_url)
    code, res = vRA.get_data(template_url)
    if code <> 200:
        logging.error("get vrealize mount cd template fail.")
        return False
    template = json.loads(res)
    logging.debug('get mount cd template success %s' % str(template))
    template["data"]['provider-connectAtPowerOn'] = connectAtPowerOn
    template["data"]['provider-deviceType'] = MountCDdeviceType[deviceType]
    template["data"]["provider-filePath"] = vRA_ISO_Path+filePath
    action_url = get_vRealize_Machine_Actions(requestID, action=vRealizeActions['MountCD'], vRA=vRA)
    if action_url == None:
        logging.error('Get vrealize mount cd action url fail')
        return False
    logging.debug('Get vrealize mount cd url success: %s' % action_url)
    code, res = vRA.post_data(action_url, template)
    if check_action_finished(requestID, vRealizeActions['MountCDTemp'], vRA):
        logging.debug("Mount success")
        return True
    else:
        logging.error("Mount fail")
        return False

def Upload_iso(iso_location = ISO_LOCATION):
    '''
      parameter:
      using ftp to upload the iso onto vRA ftp server
      parameter:
          iso_location
    '''
    try:
        logging.debug("Now try to mount vRA smb server.")
        if not os.path.isdir(vRA_MountPoint):
            logging.debug("the %s is not a dir" % vRA_MountPoint)
            os.system("rm -f %s|mkdir %s" % (vRA_MountPoint,vRA_MountPoint))
        cmd = 'mountpoint -q %s ||mount -t cifs -o domain=%s,username="%s",password="%s" //%s %s'%(vRA_MountPoint, vRA_Domain, vRA_FTP_username, vRA_FTP_password, vRA_FTP_Server+vRA_FTP_Path, vRA_MountPoint)
        os.system(cmd)
        logging.debug("now uploading the iso file")
        cmd = 'yes|cp -f %s %s' % (iso_location, vRA_MountPoint)
        os.system(cmd)
        cmd = 'umount %s' % vRA_MountPoint
        os.system(cmd)
        return True
    except Exception as e:
        logging.error(e)
        return False

def vRA_install_ISO(virtual_machine, iso_name, iso_location=ISO_LOCATION, mount_type = 'Datastore'):
    Upload_iso(iso_location)
    vRA = VRealizeObject()
    tmp = get_vRealize_Machine_ReqID(virtual_machine, vRA=vRA)
    while True:
        test = get_latest_vRealize_Snapshot(tmp, vRA=vRA)
        if test == GoldenSnapshot:
            break
        delete_vRealize_Snapshot(tmp,test ,vRA=vRA)
    revert_vRealize_Snapshot(tmp,GoldenSnapshot ,vRA=vRA)
    power_off_vRealize_Machine(tmp, vRA=vRA)
    MountCD_vRealize_Machine(tmp, mount_type, iso_name, vRA=vRA)
    time.sleep(300)
    power_on_vRealize_Machine(tmp, vRA=vRA)

def vRA_CreateSnapshoAfterInstall(virtual_machine):
    vRA = VRealizeObject()
    tmp = get_vRealize_Machine_ReqID(virtual_machine, vRA=vRA)
    create_vRealize_Snapshot(tmp, 'fresh_install', vRA=vRA)
    test = get_latest_vRealize_Snapshot(tmp, vRA=vRA)
    with open(vRA_SnapshotFile, 'w') as outfile:
        json.dump(test, outfile)

def vRA_RevertSnapshotBeforeCase():
    with open(vRA_SnapshotFile, 'r') as snapfile:
        res = snapfile.readlines()
        snapinfo = json.loads(res[0])
    revert_vRealize_Snapshot(tmp,snapinfo,vRA=vRA)
    power_on_vRealize_Machine(tmp, vRA=vRA)



if __name__ == "__main__":
    pass



    
