import ipaddress
from ipaddress import IPv4Address

from TestBase import *
from CfgGrp_02 import *
from OneOs5_mgr import *


#################################################################################
# This module implements all the test cases of the test group 02b i.e. the test
# cases dependent on the following configuration files for the DUT and the switch
#################################################################################

_dut_cfg_name = "Group02b_DUT"
_swi_cfg_name = "Group02b_SWI"


##################################################################
# Abstract class encapsulating all the functionality needed by all
# the test cases of the test group 02b.
# This class has a pure virtual method run().
# It is defined to be inherited by test objects corresponding to
# specific test cases or combinations of test cases
##################################################################
class TestGrp_02b_Base(TestBase):

  def __init__(self, name, description):
    super(TestGrp_02b_Base, self).__init__(name = name,
                                           dut_cfg_name = _dut_cfg_name,
                                           swi_cfg_name = _swi_cfg_name,
                                           description = description)


  def _init_xmlGen(self):
    super(TestGrp_02b_Base, self)._init_xmlGen()

  def run(self):
    raise NotImplementedError


##########################################################
# Test object implementing PPA_PM_basics
##########################################################
class TestAdmin_PPA_PM_basics(TestGrp_02b_Base):

  _REBOOT_AUX5 = False

  def __init__(self, name, AUX5_connection_str):
    description = "Check PPA-PM"
    super(TestAdmin_PPA_PM_basics, self).__init__(name = name, description = description)
    self.AUX5_connection_str = AUX5_connection_str
    self.AUX5_dev = None
    self.keywords = ( 'cp_ppapm cpdm_ppapm cpdmmib_ppapm trc_user_ppapm' )

  def _init_xmlGen(self):
    super(TestAdmin_PPA_PM_basics, self)._init_xmlGen()
    self.xmlGen.oaId = '012.01'
    self.xmlGen.features_per_technology = {'management_admin': ['ppa-pm']}

  def prepare_aux_devices(self, aux_cfg_path_prefix, aux_log_stream):
    self.AUX5_dev = OneOs5_mgr("AUX5_ONE700", self.AUX5_connection_str)
    self.AUX5_dev.set_login_credentials('admin', 'admin')
    echo_prefix_fmt = alter_msg_prefix_fmt(self.log.msg_prefix_fmt, '>')
    self.AUX5_dev.set_log(aux_log_stream, echo_prefix_fmt)
    if not self.AUX5_dev.connect():
      self.log.error("Failed to connect to %s" % self.AUX5_dev.device_name)
      return False
    if self._REBOOT_AUX5:
      self.AUX5_dev.reconnect_delay = 120.0
      return (	  self.AUX5_dev.reboot(isEchoOn = True)
                    and self.AUX5_dev.config_after_boot(isEchoOn = True))
    else:
      return True

  def startPPAPMSessions (self, ppapmListToStart):
    cfg_str = ''
    for ppapmNb in ppapmListToStart:
      cfg_str += ' ppa-pm schedule %s start now\n' % ppapmNb

    return self.dut_mgr.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)

  def stopPPAPMSessions (self, ppapmListToStop):
    cfg_str = ''
    for ppapmNb in ppapmListToStop:
      cfg_str += ' no ppa-pm schedule %s\n' % ppapmNb

    return self.dut_mgr.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)

  def startPPAPMSessionsAUX (self, ppapmListToStart):
    cfg_str = ''
    for ppapmNb in ppapmListToStart:
      cfg_str += ' ppa-pm schedule %s start now\n' % ppapmNb

    return self.AUX5_dev.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)

  def stopPPAPMSessionsAUX (self, ppapmListToStop):
    cfg_str = ''
    for ppapmNb in ppapmListToStop:
      cfg_str += ' no ppa-pm schedule %s\n' % ppapmNb

    return self.AUX5_dev.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)

  def checkPPAPMSessions (self, ppapmListToStop):
    isPass = True

    for ppapmNb in ppapmListToStop:
      self.dut_mgr.send_cmd('show ppa-pm session %s operational-state' % ppapmNb)
      session = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'PPA-PM')
      if session == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve state for PPA-PM session %s' % ppapmNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm session %s operational-state' % ppapmNb, isEchoOn = True)
        break
      status = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'completion')
      if status == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve status for PPA-PM session %s' % ppapmNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm session %s operational-state' % ppapmNb, isEchoOn = True)
        break
      roundtrip = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'round-trip')
      if roundtrip == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve round-trip values for PPA-PM session %s' % ppapmNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm session %s operational-state' % ppapmNb, isEchoOn = True)
        break
      self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = self.dut_mgr.target_prompt_re)
      session_state = scan_line (session, '[(](.+)[)]')
      session_state_ok = (session_state is not None and session_state == 'active')
      status_value = scan_line (status, ':\s*(.+)')
      if status_value: status_value = status_value.rstrip()
      status_value_ok = (status_value is not None and status_value == 'ok')
      matchobj = scan_line_matchobj(roundtrip, '(\d+)avg, (\d+)sum, (\d+)min, (\d+)max')
      avgV = parse_counter(nice_getmatch(matchobj, 1))
      avgV_ok = (avgV is not None)
      sumV = parse_counter(nice_getmatch(matchobj, 2))
      sumV_ok = (sumV is not None)
      minV = parse_counter(nice_getmatch(matchobj, 3))
      minV_ok = (minV is not None)
      maxV = parse_counter(nice_getmatch(matchobj, 4))
      maxV_ok = (maxV is not None)
      isPassTmp = all ([session_state_ok, status_value_ok, avgV_ok, sumV_ok, minV_ok, maxV_ok])
      isPass = isPass and isPassTmp
      fmt_str = "Result of PPA-PM session %3s : state %s / status %s / avg round-trip is %sms (min:%sms max:%sms)"
      self.log.comment(fmt_str % (ppapmNb,
                                  nice_str(session_state, not session_state_ok),
                                  nice_str(status_value, not status_value_ok),
                                  nice_str(avgV, not avgV_ok),
                                  nice_str(minV, not minV_ok),
                                  nice_str(maxV, not maxV_ok)))
      if isPassTmp is False :
        self.log.error("Unexpected result")
      if not all ([session_state_ok, status_value_ok, avgV_ok, sumV_ok, minV_ok, maxV_ok]):
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm session %s operational-state' % ppapmNb, isEchoOn = True)

    return isPass

  def checkPPAPMResponder (self):
    isPass = True

    portList = [('63001'),('63002'),('63003'),('63004'),('63005'),('64001'),('64002'),('64003'),('64004'),('64005')]

    for portNb in portList:
      self.dut_mgr.send_cmd('show ppa-pm responder %s' % portNb)
      status = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'PPAPM')
      if status == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve status for PPA-PM responder on port %s' % portNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm responder %s' % portNb, isEchoOn = True)
        break
      receivedT = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'TIMESTAMP')
      if receivedT == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve received packets for PPA-PM responder on port %s' % portNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm responder %s' % portNb, isEchoOn = True)
        break
      sentT = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = 'TIMESTAMP')
      if sentT == '':
        self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
        isPass = False
        self.log.error('Failed to retrieve sent packets for PPA-PM responder on port %s' % portNb)
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm responder %s' % portNb, isEchoOn = True)
        break
      self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = False, match_re = self.dut_mgr.target_prompt_re)
      status_value = scan_line (status, ':\s*(.+)')
      if status_value: status_value = status_value.rstrip()
      status_value_ok = (status_value is not None and status_value == 'running')
      receivedT_value = scan_line (receivedT, ':\s*(.+)')
      if receivedT_value: receivedT_value = receivedT_value.rstrip()
      receivedT_value_ok = (receivedT_value is not None and receivedT_value != '0')
      sentT_value = scan_line (sentT, ':\s*(.+)')
      if sentT_value: sentT_value = sentT_value.rstrip()
      sentT_value_ok = (sentT_value is not None and sentT_value != '0' and sentT_value == receivedT_value)
      isPassTmp = all ([status_value_ok, receivedT_value_ok, sentT_value_ok])
      isPass = isPass and isPassTmp
      fmt_str = "Result of PPA-PM responder on port %s : status %s / received UTS packets: %s / sent UTS packets: %s)"
      self.log.comment(fmt_str % (portNb,
                                  nice_str(status_value, not status_value_ok),
                                  nice_str(receivedT_value, not receivedT_value_ok),
                                  nice_str(sentT_value, not sentT_value_ok)))
      if isPassTmp is False :
        self.log.error("Unexpected result")
      if not all ([status_value_ok, receivedT_value_ok, sentT_value_ok]):
        self.dut_mgr.send_cmd_and_get_rsp('show ppa-pm responder %s' % portNb, isEchoOn = True)

    return isPass

  def run(self):
    isPass = True

    #When/if PRT-24226 is fixed, session : ('121'),('122'),('123'),('124'),('125') could be added
    ppapmList = [('1')  ,('2')  ,('3')  ,('4')  ,('5')  ,('11') ,('12') ,('13') ,('14') ,('15') ,
                 ('101'),('102'),('103'),('104'),('105') ]

    ppapmListAUX = [('1'),('2'),('3'),('4'),('5'),('101'),('102'),('103'),('104'),('105') ]

    isPass = isPass and self.startPPAPMSessions(ppapmList)
    isPass = isPass and self.startPPAPMSessionsAUX(ppapmListAUX)
    self.log.comment("Wait 20s for PPA-PM to update")
    self.dut_mgr.wait_for_input(timeout=10, isEchoOn=True)
    self.log.comment("10s")
    self.dut_mgr.wait_for_input(timeout=10, isEchoOn=True)
    self.log.comment("Done")
    isPass = self.checkPPAPMSessions(ppapmList) and isPass
    isPass = self.checkPPAPMResponder() and isPass
    isPass = self.stopPPAPMSessions(ppapmList) and isPass
    isPass = self.stopPPAPMSessionsAUX(ppapmListAUX) and isPass

    isPass = self.check_DUT_end_of_test() and isPass

    self.print_passorfail(isPass)
    return isPass

##########################################################
# Test object implementing POE_basics
##########################################################
class TestPOE_basics(TestGrp_02b_Base):

  def __init__(self, name):
    description = "Check POE"
    super(TestPOE_basics, self).__init__(name = name, description = description)
    self.retries  = 6
  #    self.keywords = "cp_hwmgr"

  def _init_xmlGen(self):
    super(TestPOE_basics, self)._init_xmlGen()
    self.xmlGen.oaId = '012.02'
    self.xmlGen.features_per_technology = {'lan_wan_interfaces': ['poe']}

  def prepare_aux_devices(self, aux_cfg_path_prefix, aux_log_stream):
    return True

  def checkPowerItf(self, interfaceToCheck = "2/4", powerValue = "auto"):
    isPass = True

    self.dut_mgr.send_cmd('show power inline interface gigabitethernet %s' % interfaceToCheck)
    entry = self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True, match_re = "Port")
    entry = self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True, match_re = interfaceToCheck)
    if entry is not None :
      operStatus = scan_line (entry, '%s\s+%s\s+(\S+)' % (interfaceToCheck,powerValue))
      if powerValue == "off" :
        operStatus_ok = (operStatus is not None) and (operStatus == "off")
      else :
        operStatus_ok = (operStatus is not None) and (operStatus == "on")

      isPass = operStatus_ok
      fmt_str = "Interface gigabitethernet %s power configuration : set to %s : OperStatus is %s"
      self.log.comment(fmt_str % (interfaceToCheck,
                                  powerValue,
                                  nice_str(operStatus, not operStatus_ok)))
      if isPass is False :
        self.log.error("Unexpected result")
    else :
      self.log.error("No entry found")
      isPass = False

    return isPass

  def setPowerOnItf(self, interfaceToPower = "gigabitethernet 2/4", powerValue = "auto"):
    isPass = True

    cfg_str_fmt = ( 'interface %s\n'
                    + ' power inline mode %s\n'
                    + 'exit' )
    cfg_str = cfg_str_fmt % (interfaceToPower,powerValue)

    isPass = self.dut_mgr.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)
    if not isPass:
      self.log.error('Failed to set power mode %s on interface %s' % (powerValue,interfaceToPower))

    return isPass

  def checkPingQuery(self, hostToPing = "200.0.0.10", interfaceUp = True):
    self.dut_mgr.send_cmd('ping %s' % hostToPing)
    line = self.dut_mgr.wait_for_input(timeout = 30.0, isEchoOn = True, match_re = 'Success rate is')
    if line == '':
      self.dut_mgr.term.write("\x03") # Timeout elapsed, so send ^C
    self.dut_mgr.wait_for_input(timeout = 4.0, isEchoOn = True, match_re = self.dut_mgr.target_prompt_re)
    matchobj = scan_line_matchobj(line, 'Success rate is [0-9.]+ percent [(](\d+)[/](\d+)[)]')
    pkts_received = parse_counter(nice_getmatch(matchobj, 1))
    pkts_sent = parse_counter(nice_getmatch(matchobj, 2))
    pkts_sent_ok = (pkts_sent is not None and pkts_sent == 5)
    if (interfaceUp) :
      pkts_received_ok = (    pkts_received is not None
                              and pkts_received >= 4)
    else :
      pkts_received_ok = (    pkts_received is not None
                              and pkts_received == 0)

    isPass = pkts_sent_ok and pkts_received_ok
    fmt_str = "Result of ping to %s : sent %s, received %s"
    self.log.comment(fmt_str % (str(hostToPing),
                                nice_str(pkts_sent, not pkts_sent_ok),
                                nice_str(pkts_received, not pkts_received_ok)))
    if isPass is False :
      self.log.error("Unexpected result")
    return isPass

  def run(self):
    isPass = True
    self.log.comment("<=== POE basics")

    addressList = [ ('200.1.0.10'), ('200.0.0.10') ]
    upWait = 60

    self.log.comment("Test 1 : Check POE equipments are alive when seting power set to auto")
    isPass = isPass and self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/2", powerValue = "auto")
    isPass = isPass and self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/4", powerValue = "auto")

    self.log.comment("Wait %ss for equipments to be operationnal" % (upWait))
    remainTime = upWait
    while (remainTime > 0):
      self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True)
      remainTime -= 10
      self.log.comment("%ss" % (remainTime))

    isPass = self.checkPowerItf("2/2","auto")       and isPass
    isPass = self.checkPowerItf("2/4","auto")       and isPass
    for addressToTest in addressList:
      isPassPartial = self.checkPingQuery(addressToTest,True)
      if not isPassPartial:
        self.log.warning("Retry %d time(s)" % self.retries)
        for _ in range(self.retries):
          self.log.comment("Wait 10s")
          self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True)
          isPassPartial = self.checkPingQuery("200.1.0.10",True)
          if isPassPartial:
            break
      isPass = isPassPartial and isPass

    self.log.comment("Test 2 : Check POE equipments are not alive when setting power to never")
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/2", powerValue = "never") and isPass
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/4", powerValue = "never") and isPass
    self.dut_mgr.wait_for_input(timeout = 2.0, isEchoOn = True)
    isPass = self.checkPowerItf("2/2","off")         and isPass
    isPass = self.checkPowerItf("2/4","off")         and isPass
    isPass = self.checkPingQuery("200.1.0.10",False) and isPass
    isPass = self.checkPingQuery("200.0.0.10",False) and isPass

    self.log.comment("Test 3 : Check POE equipments are alive when setting power to static")
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/2", powerValue = "static") and isPass
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/4", powerValue = "static") and isPass

    self.log.comment("Wait %ss for equipments to be operationnal" % (upWait))
    remainTime = upWait
    while (remainTime > 0):
      self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True)
      remainTime -= 10
      self.log.comment("%ss" % (remainTime))

    isPass = self.checkPowerItf("2/2","static")     and isPass
    isPass = self.checkPowerItf("2/4","static")     and isPass
    for addressToTest in addressList:
      isPassPartial = self.checkPingQuery(addressToTest,True)
      if not isPassPartial:
        self.log.warning("Retry %d time(s)" % self.retries)
        for _ in range(self.retries):
          self.log.comment("Wait 10s")
          self.dut_mgr.wait_for_input(timeout = 10.0, isEchoOn = True)
          isPassPartial = self.checkPingQuery("200.1.0.10",True)
          if isPassPartial:
            break
      isPass = isPassPartial and isPass

    self.log.comment("Disable POE equipments")
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/2", powerValue = "never") and isPass
    isPass = self.setPowerOnItf(interfaceToPower = "gigabitethernet 2/4", powerValue = "never") and isPass

    isPass = self.check_DUT_end_of_test() and isPass

    self.print_passorfail(isPass)
    return isPass

##########################################################
# Test object implementing EventDrivenConf_Basics
##########################################################
class TestAdmin_EventDrivenConf_Basics(TestGrp_02b_Base):

  def __init__(self, name):
    description = "Check Event Driven"
    super(TestAdmin_EventDrivenConf_Basics, self).__init__(name = name, description = description)
    self.keywords = "cp_eemgr cplib_eemgr"

  def _init_xmlGen(self):
    super(TestAdmin_EventDrivenConf_Basics, self)._init_xmlGen()
    self.xmlGen.oaId = '012.03'
    self.xmlGen.features_per_technology = {'management_admin': ['eem']}

  def prepare_aux_devices(self, aux_cfg_path_prefix, aux_log_stream):
    return True

  def getDeviceName(self):
    self.dut_mgr.send_cmd('show system hardware')
    entry = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = True, match_re = "Device\s*:")

    if entry is not None :
      deviceName = scan_line (entry, 'Device\s*:\s*(\S+)')
      if deviceName is not None :
        self.log.comment("Device name %s" % deviceName)
      else :
        self.log.error("Unable to find device name in %s" % entry)
    else :
      self.log.error("Unable to find device name in show system hardware")
      deviceName = None

    self.dut_mgr.wait_for_input(timeout = 4.0, isEchoOn = True, match_re = self.dut_mgr.target_prompt_re)
    return deviceName

  def changeInterfaceParam(self, interface, param):
    isPass = True
    cfg_str_fmt = ( 'interface %s\n'
                    + ' %s\n'
                    + 'exit' )
    cfg_str = cfg_str_fmt % (interface,param)

    isPass = self.dut_mgr.configure_terminal(cfg_str, isConfirmRequired = False, isEchoOn = True)
    if not isPass:
      self.log.error('Failed to set %s on interface %s' % (param,interface))

    return isPass

  def checkItfDescription(self, interfaceToCheck, device, description):
    isPass = True

    self.dut_mgr.send_cmd('show interface %s' % interfaceToCheck)
    entry = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = True, match_re = "Description:")
    self.dut_mgr.wait_for_input(timeout = 4.0, isEchoOn = True, match_re = self.dut_mgr.target_prompt_re)

    if entry is not None :
      desc_found = scan_line (entry, 'Description\:.*%s.*(%s)' % (device,description))
      if desc_found is not None :
        self.log.comment("Description matches (%s) %s" % (device,description))
      else :
        self.log.error("Description doesn't match (%s) %s" % (device,description))
        isPass = False
    else :
      self.log.error("No description found on interface %s" % interfaceToCheck)
      isPass = False

    return isPass

  def run(self):
    isPass = True
    self.log.comment("<=== Event Driven Configuration basics")

    deviceName = self.getDeviceName()
    if self.dut_mgr.device_name == 'ONE1651':
      iface_name = "GigabitEthernet 0/4"
    elif self.dut_mgr.device_name == 'ONE526S':
      iface_name = "GigabitEthernet 0/1"
    else:
      iface_name = "GigabitEthernet 0/2"
    isPass = self.changeInterfaceParam(interface = iface_name, param = "description ------ (%s) Interface NOT CHANGED ------" % deviceName) and isPass
    isPass = self.checkItfDescription(interfaceToCheck = iface_name, device = deviceName, description = "NOT CHANGED") and isPass

    isPass = self.changeInterfaceParam(interface = iface_name, param = "shutdown") and isPass
    # It is necessary to grant enough time to let the event be triggered due to DB update (5s + 1s monitoring)
    self.dut_mgr.wait_for_input(timeout=6, isEchoOn=True) and isPass
    isPass = self.checkItfDescription(interfaceToCheck = iface_name, device = deviceName, description = "DOWN") and isPass

    isPass = self.changeInterfaceParam(interface = iface_name, param = "description ------ (%s) Interface NOT CHANGED ------" % deviceName) and isPass
    isPass = self.changeInterfaceParam(interface = iface_name, param = "no shutdown") and isPass
    # It is necessary to grant enough time to let the event be triggered due to DB update (9s + 1s monitoring)
    self.dut_mgr.wait_for_input(timeout=10, isEchoOn=True)
    isPass = self.checkItfDescription(interfaceToCheck = iface_name, device = deviceName, description = "UP") and isPass

    self.dut_mgr.send_cmd('event manager run applet-3')
    self.dut_mgr.wait_for_input(timeout = 2.0, isEchoOn = True, match_re = self.dut_mgr.target_prompt_re)
    # It is necessary to grant enough time to let the event be triggered due to DB update (5s + 1s monitoring)
    self.dut_mgr.wait_for_input(timeout=6, isEchoOn=True)

    isPass = self.checkItfDescription(interfaceToCheck = iface_name, device = deviceName, description = "MANUAL") and isPass
    # The line above triggers a 10s timer to launch applet-4
    self.dut_mgr.wait_for_input(timeout=10, isEchoOn=True)
    isPass = self.checkItfDescription(interfaceToCheck = iface_name, device = deviceName, description = "TIMER") and isPass

    isPass = self.changeInterfaceParam(interface = iface_name, param = "no description") and isPass
    self.dut_mgr.wait_for_input(timeout = 2.0, isEchoOn = True, match_re = self.dut_mgr.target_prompt_re)

    isPass = self.check_DUT_end_of_test() and isPass

    self.print_passorfail(isPass)
    return isPass

##########################################################
# Test object implementing Administration_ShowFiltering
##########################################################
class TestAdministration_ShowFiltering(TestGrp_02b_Base):

  def __init__(self, name):
    description = "Check Event Driven"
    super(TestAdministration_ShowFiltering, self).__init__(name = name, description = description)
    self.keywords = "trc_event_data cp_logd cpdm_log"
    self.debugInfo = True

  def _init_xmlGen(self):
    super(TestAdministration_ShowFiltering, self)._init_xmlGen()
    self.xmlGen.oaId = '012.04'
    self.xmlGen.features_per_technology = {'management_admin': ['show']}

  def prepare_aux_devices(self, aux_cfg_path_prefix, aux_log_stream):
    return True

  def restoreEquipment(self):
    self.dut_mgr.term.send_cmd("rm /sh_pia_save.txt")
    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)
    self.dut_mgr.term.send_cmd("rm /sh_pia_append.txt")
    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)

  def __checkFilter(self, cmd, caseNumber, nb_mac):
    retVal = True

    if caseNumber == 1:
      if nb_mac == 4:
        values = [(1,0),(2,1),(3,2),(4,3)]
      else:
        values = [(1,0),(2,1),(3,2),(4,3),(5,4),(6,5),(7,6),(8,7)]
    elif caseNumber == 2:
      if nb_mac == 4:
        values = [(1,1),(2,2),(3,4)]
      else:
        values = [(1,1),(2,2),(3,3),(4,5),(5,6)]
    else:
      if nb_mac == 4:
        values = [(1,0),(2,1),(3,2),(4,3),(5,1),(6,2),(7,4)]
      else:
        values = [(1,0),(2,1),(3,2),(4,3),(5,4),(6,5),(7,6),(8,7),(9,1),(10,2),(11,3),(12,5),(13,6)]

    self.dut_mgr.term.send_cmd(cmd)
    line = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = cmd)
    for i,j in values:
      line = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = '.*')
      if line is None or line == "":
        self.log.error('Show failed at line %d' %i)
        retVal = False
      elif ("mac%d" %j) not in line:
        self.log.error('Show failed at line %d' %i)
        retVal = False
      elif ((caseNumber == 2) and ("%d:" %i) not in line):
        self.log.error('Show failed at line %d (linnum)' %(j))
        retVal = False
      elif self.debugInfo:
        self.log.comment("Found line %i : %s" % (i,line))

    line = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = '.*')
    if (self.dut_mgr.target_prompt) not in line:
      self.log.error('Extra show after last line expected : %s' % (line))
      self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)
      retVal = False
    return retVal

  def checkFilterBeginUntilInclude(self, nb_mac):
    retVal = True

    if nb_mac == 4:
      cmd_show = "show product-info-area | begin mac0 | until mac3 | include mac"
    else:
      cmd_show = "show product-info-area | begin mac0 | until mac7 | include mac"
    retVal = self.__checkFilter(cmd_show,1,nb_mac)

    if nb_mac == 4:
      cmd_show = "show product-info-area | begin mac0 | until mac3 | include mac | count"
      cmd_count = 4
    else:
      cmd_show = "show product-info-area | begin mac0 | until mac7 | include mac | count"
      cmd_count = 8
    self.dut_mgr.term.send_cmd(cmd_show)
    line = self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = 'Count\:')
    if line is None or line == "":
      self.log.error('Count failed')
      retVal = False
    else:
      nbFound = parse_int(scan_line(line, "Count\s*\:\s*(\d+)"), isNonNegative=True)
      if nbFound != cmd_count:
        self.log.error('Wrong count : %d instead of %d' % (nbFound,cmd_count))
        retVal = False
      elif self.debugInfo:
        self.log.comment("Count OK")

    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)
    return retVal

  def checkFilterBeginAtLineCount(self, nb_mac):
    retVal = True

    if nb_mac == 4:
      cmd_show = "show product-info-area | beginAt 2 mac | until mac4 | include mac | exclude mac3 | linnum"
    else:
      cmd_show = "show product-info-area | beginAt 2 mac | until mac6 | include mac | exclude mac4 | linnum"
    retVal = self.__checkFilter(cmd_show,2,nb_mac)

    return retVal

  def checkFilterFileManagement(self, nb_mac):
    retVal = True

    if nb_mac == 4:
      cmd_show1 = "show product-info-area | begin mac0 | until mac3 | include mac | save /sh_pia_save.txt"
      cmd_show2 = "show product-info-area | begin mac0 | until mac3 | include mac | append /sh_pia_append.txt"
      cmd_show3 = "show product-info-area | beginAt 2 mac | until mac4 | include mac | exclude mac3 | append /sh_pia_append.txt"
    else:
      cmd_show1 = "show product-info-area | begin mac0 | until mac7 | include mac | save /sh_pia_save.txt"
      cmd_show2 = "show product-info-area | begin mac0 | until mac7 | include mac | append /sh_pia_append.txt"
      cmd_show3 = "show product-info-area | beginAt 2 mac | until mac6 | include mac | exclude mac4 | append /sh_pia_append.txt"
    self.dut_mgr.term.send_cmd(cmd_show1)
    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)
    self.dut_mgr.term.send_cmd(cmd_show2)
    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)
    self.dut_mgr.term.send_cmd(cmd_show3)
    self.dut_mgr.wait_for_input(timeout = 5.0, isEchoOn = self.debugInfo, match_re = self.dut_mgr.target_prompt_re)

    retVal = self.__checkFilter("cat /sh_pia_save.txt",1,nb_mac)
    retVal = self.__checkFilter("cat /sh_pia_append.txt",3,nb_mac) and retVal

    return retVal

  def run(self):
    isPass = True
    self.log.comment("<=== Administration Show Filtering")

    if self.dut_mgr.target_prompt_re is None:
      self.log.error("Testcase cannot run without a valid prompt, abort")
      self.print_passorfail(False)
      return False

    nb_mac_line = self.dut_cfg_lines.get('max_mac', None)
    nb_mac = parse_int(scan_line(nb_mac_line, "max_mac\s(\d+)"), isNonNegative=True)
    assert nb_mac is not None, "DUT config file must contain marker $CIT max_mac with a valid integrer value"
    self.log.comment( "Number of mac addresses : %d" % nb_mac)

    self.restoreEquipment()

    self.log.comment(  '\n+-----------------------------------------------+'
                       + '\n| Checking filters begin, until, include, count |'
                       + '\n+-----------------------------------------------+')
    isPassTest = self.checkFilterBeginUntilInclude(nb_mac)
    isPass = isPassTest and isPass
    if isPassTest:
      self.log.comment("  --- OK")
    else:
      self.log.error("  --- FAIL")

    self.log.comment(  '\n+-------------------------------------------------+'
                       + '\n| Checking filters beginAt, until, exclude, linum |'
                       + '\n+-------------------------------------------------+')
    isPassTest = self.checkFilterBeginAtLineCount(nb_mac)
    isPass = isPassTest and isPass
    if isPassTest:
      self.log.comment("  --- OK")
    else:
      self.log.error("  --- FAIL")

    self.log.comment(  '\n+----------------------------------+'
                       + '\n| Checking filters file management |'
                       + '\n+----------------------------------+')
    isPassTest = self.checkFilterFileManagement(nb_mac)
    isPass = isPassTest and isPass
    if isPassTest:
      self.log.comment("  --- OK")
    else:
      self.log.error("  --- FAIL")

    self.restoreEquipment()

    isPass = self.check_DUT_end_of_test() and isPass

    self.print_passorfail(isPass)
    return isPass


##########################################################
# Test object implementing Ping
##########################################################
class TestPing_Basics(TestGrp_02b_Base):

  def __init__(self, name, AUX5_connection_str):
    description = "Check Ping"
    super(TestPing_Basics, self).__init__(name = name, description = description)
    self.keywords = "ping"
    self.keywords = "ping6"
    self.debugInfo = True

  def _init_xmlGen(self):
    super(TestPing_Basics, self)._init_xmlGen()
    self.xmlGen.oaId = '012.04'
    self.xmlGen.features_per_technology = {'management_admin': ['ping']}

  def prepare_aux_devices(self, aux_cfg_path_prefix, aux_log_stream):
    return True

  def _check_ping_result(self, target_addr, target_name, ping_options = None, loss_rate_max = 10):
    #self.log.error('Entered check Ping result with parameters: %s | %s | %s | %s' % (target_addr, target_name, count, loss_rate_max))
    ping_result = self.dut_mgr.ping(target=target_addr,
                                    options=ping_options,
                                    timeout=10)
                                    #timeout1=0.3 * Count)

    success_rate = parse_counter(scan_line(ping_result, 'Success rate is (\d+) percent'))

    if success_rate is None:
      loss_rate = None
    else:
      loss_rate = 100 - success_rate

    loss_rate_ok = (loss_rate is not None) and (loss_rate <= 100 * loss_rate_max)
    loss_rate_str = nice_str(loss_rate, not loss_rate_ok, '%d%%')

    if loss_rate_ok:
      self.log.comment('Ping to %s successful, loss rate: %s' % (target_name, loss_rate_str))
    else:
      self.log.error('Ping to %s failed, loss rate: %s' % (target_name, loss_rate_str))
      return False
    return True

  def run(self):
    # isPass = True
    # self.log.comment("<=== Ping")
    #
    # isPass = self.check_DUT_end_of_test() and isPass
    #
    # self.print_passorfail(isPass)
    #self.dut_mgr
    target_ipv4_addr = ipaddress.ip_address(u'220.2.4.12')
    target_ipv4_vrf_addr = ipaddress.ip_address(u'60.0.0.10')
    unknow_addr_ipv4 = ipaddress.ip_address(u'112.212.1.2')
    target_name = 'DUT'
    loss_rate_max = 10
    isPass = True

    self.log.comment("*** Test 01 : Testing default IPv4 ping \n \n")
    result = self._check_ping_result(target_ipv4_addr, target_name, '')
    if result is False:
      isPass = False
      self.log.comment("*** Test 01 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 01 : OK *** \n \n \n")

    self.log.comment("*** Test 02 : Testing IPv4 ping with size 20000 \n \n")
    result = self._check_ping_result(target_ipv4_addr, target_name, '-l %d' % 20000)
    if result is False:
      isPass = False
      self.log.comment("*** Test 02 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 01 : OK *** \n \n \n")

    self.log.comment("*** Test 03 : Testing IPv4 ping with 100 pings \n \n")
    result = self._check_ping_result(target_ipv4_addr, target_name, '-n %d' % 100)
    if result is False:
      isPass = False
      self.log.comment("*** Test 02 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 01 : OK *** \n \n \n")

    self.log.comment("*** Test 04 : Testing IPv4 ping with VRF option \n \n")
    result = self._check_ping_result(target_ipv4_vrf_addr, target_name, 'vrf %s' % 'forwarding1')
    if result is False:
      isPass = False
      self.log.comment("*** Test 04 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 04 : OK *** \n \n \n")

    self.log.comment("*** Test 05 : Testing IPv4 ping with options minsize 1400, maxsize 1600 step 1 \n \n")
    result = self._check_ping_result(target_ipv4_addr, target_name,
                                     'minsize {:d} maxsize {:d} step {:d} -w 1'.format(1400, 1600, 1))
    if result is False:
      isPass = False
      self.log.comment("*** Test 05 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 05 : OK *** \n \n \n")

      self.log.comment("*** Test Unknown-ipv4-Address : Testing default IPv4 ping \n \n")
      result = self._check_ping_result(unknow_addr_ipv4, target_name, '')
      if result is True:
        isPass = False
        self.log.comment("*** Test Unknown-Address : FAIL *** \n \n \n")
      else:
        self.log.comment("*** Test Unknown-Address : OK *** \n \n \n")

    ########################
    #      IPv6 Pings       #
    ########################

    target_ipv6_addr = ipaddress.ip_address(u'223::1')
    target_ipv6_vrf_addr = ipaddress.ip_address(u'60.0.0.10')
    target_unknown = 'www.google.com'
    target_hostname = '11os6.dyndns.org'
    unknow_addr_ipv6 = ipaddress.ip_address(u'12::10')

    self.log.comment("*** Test 06 : Testing default IPv6 ping \n \n")
    result = self._check_ping_result(target_ipv6_addr, target_name, '')
    if result is False:
      isPass = False
      self.log.comment("*** Test 06 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 06 : OK *** \n \n \n")

    self.log.comment("*** Test 07 : Testing default IPv6 with ping size 2000 \n \n")
    result = self._check_ping_result(target_ipv6_addr, target_name, 'size %d' % 20000)
    if result is False:
      isPass = False
      self.log.comment("*** Test 07 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 07 : OK *** \n \n \n")

    self.log.comment("*** Test 08 : Testing default IPv6 ping with 100 pings \n \n")
    result = self._check_ping_result(target_ipv6_addr, target_name, 'repeat %d' % 100)
    if result is False:
      isPass = False
      self.log.comment("*** Test 08 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 08 : OK *** \n \n \n")



    self.log.comment("*** Test 09 : Testing default IPv6 ping with VRF option \n \n")
    result = self._check_ping_result(target_ipv6_vrf_addr, target_name, 'vrf %s' % 'forwarding')
    if result is False:
      isPass = False
      self.log.comment("*** Test 09 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 09 : OK *** \n \n \n")

    self.log.comment("*** Test 10 : Testing default IPv6 ping with options minsize 1400, maxsize 1600 step 1 \n \n")
    result = self._check_ping_result(target_ipv6_addr, target_name,
                                     'minsize {:d} maxsize {:d} step {:d} timeout 1'.format(1400, 1600, 1))
    if result is False:
      isPass = False
      self.log.comment("*** Test 10 : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test 10 : OK *** \n \n \n")

    self.log.comment("*** Test Unknown-ipv6-Address : Testing default IPv4 ping \n \n")
    result = self._check_ping_result(unknow_addr_ipv6, target_name, '')
    if result is True:
      isPass = False
      self.log.comment("*** Test Unknown-Address : FAIL *** \n \n \n")
    else:
      self.log.comment("*** Test Unknown-Address : OK *** \n \n \n")

    self.print_passorfail(isPass)
    return isPass

# export only usefull test cases, not abstract classes or intermediate definitions



__all__ = [
  'TestAdmin_PPA_PM_basics',
  'TestPOE_basics',
  'TestAdmin_EventDrivenConf_Basics',
  'TestAdministration_ShowFiltering',
  'TestPing_Basics'
]

