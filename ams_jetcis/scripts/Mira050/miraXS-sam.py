'''
    MiraXS_API usage example for analog tests.
    These examples are not tested and probably don't result in something useful,
    but they are just here to give some insights in how to setup a test case.

    Sam Melsen
    ams Sensors Belgium
'''
import traceback
import time
import statistics
import math
import numpy as np
import matplotlib.pyplot as plt

from validation_hal.mira_xs_api import MiraXS_API
from validation_hal.mira_xs_user_inputs import NameBasedProgrammingSequence, SensorControlMode, TdigUserInputs
from util.util_wgen import UtilWgen
from util.initial_upload import *
from util.util_images import UtilImages
from util.wgen import CreateWgenProg

from validation_hal.hw_interface.pxi.simplesensorctrlintf import *
from validation_hal.hw_interface.deltatec.ip.bus import GenericBus
from validation_hal.hw_interface.deltatec.ip.regmap_definitions import definitions
# A test case is just a Python function that takes one argument: a handle to the
# Mira-XS API.
# class MiraXsSupplies(Supplies):
#     def __init__(self,mira_xs_api: MiraXS_API):
#         super().__init__()
#         with SuppliesCollector(self):
#             self.VDD12 = mira_xs_api.val_api.GetSupplyObject('VDD12')
#             self.VDD18 = mira_xs_api.val_api.GetSupplyObject('VDD18')
#             self.VDD28 = mira_xs_api.val_api.GetSupplyObject('VDD28')
#         self._smu_channels=[self.VDD12,self.VDD18,self.VDD28]
def test_bringup_Ali(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State
    # Lines below is a temp solution to prevent req_exp stays high
    bus = {'axi_offset': 0x70000,
           'axi_read': mira_xs_api.val_api.AxiRead,
           'axi_write': mira_xs_api.val_api.AxiWrite,
           'type': 'axi'}
    regbus = GenericBus(bus_definition=bus, prefix='axi_')
    simple_sensor_ctrl_intf = SimpleSensorCtrlIntf(regbus)

    # Make REQ_EXP and REQ_FRAME low
    simple_sensor_ctrl_intf.initialize_sensor_timing()
    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT #stream mode
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 0
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 33333
    # mira_xs_api.default_VDD18 = 1.25
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    # util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_colload_constant.txt")
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_cur_starv.txt")

    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    input('please power on VDD28')
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    mira_xs_api.upload_context('A')

    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)
    # Manual tweaking

    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN    
    mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    mira_xs_api.write_register('VDAC_SET_3', 200) # VR0
    mira_xs_api.write_register('VDAC_SET_4', 180) # VS0

    mira_xs_api.write_register('VDAC_SET_0', 231) # VRAMPREF
    mira_xs_api.write_register('VDAC_SET_1', 225) # VCOMPREF (CDS)
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)

    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 14)
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 4)

    tdig_seq = NameBasedProgrammingSequence()
    tdigs = TdigUserInputs(1, "LOG_CSI2_TX", "HSYNC")
    tdig_seq.add_sequence(tdigs.generate_programming_sequence())
    tdigs = TdigUserInputs(2, "LOG_CSI2_TX", "VSYNC")
    tdig_seq.add_sequence(tdigs.generate_programming_sequence())
    tdigs = TdigUserInputs(3, "LOG_MASTER", "LPS_ACTIVE")
    tdig_seq.add_sequence(tdigs.generate_programming_sequence())
    mira_xs_api.upload_programming_sequence(tdig_seq)

    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    # POWER measurement
   # for i in range(100):
    #    for ps in ['VDD28', 'VDD12', 'VDD18']:
     #       print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)} A")
    input('press any key to disable ANAMUXs')
    mira_xs_api.write_register('AMUX_EN', 0)
    mira_xs_api.write_register('AMUX2_EN', 0)    
    input('press any key to disable adcana')
    mira_xs_api.write_register('ADCANA_BIAS_BUF_EN', 0)
    mira_xs_api.write_register('BSP_COMP_EN', 0)
    input('press any key to disable rampgen')
    mira_xs_api.write_register('RAMP_VREF_EN', 0)
    mira_xs_api.write_register('RAMP_VRAMP_EN', 0)
    input('press any key to disable rowdrivers')
    mira_xs_api.write_register('ROWDG_EN', 0)
    mira_xs_api.write_register('ROWDR_EN', 0)
    input('press any key to disable bias_block')
    mira_xs_api.write_register('BIAS_IREF_EN', 0)
    mira_xs_api.write_register('BIAS_VDAC_VREF_EN', 0)
    mira_xs_api.write_register('IDAC_EN', 0)
    input('press any key to disable colload_local_buf')
    mira_xs_api.write_register('COL_BIAS_BUFF_EN', 0)

    input('press any key to continue')
    
def test_bringup_Adi(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_rowdriver.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'TG' : 'GLOB_SMP'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)
    # Manual tweaking

    #mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    #mira_xs_api.write_register('EXT_YADDR', 815)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)
    mira_xs_api.write_register('ROWDG_SLEW_TX', 1)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 1) #FOR TEST_MODE SHOULD BE DISABLED
    #mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN    
    #mira_xs_api.write_register('COL_TEST_EN', 0) # Force known voltages on the column bus
    mira_xs_api.write_register('VDAC_SET_3', 200) # VR0
    mira_xs_api.write_register('VDAC_SET_4', 180) # VS0

    mira_xs_api.write_register('VDAC_SET_0', 231) # VRAMPREF
    mira_xs_api.write_register('VDAC_SET_1', 225) # VCOMPREF (CDS)
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)

    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 4)
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 10)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_bias(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_colload_constant.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)
    # Manual tweaking
    
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('VDAC_SET_1', 225) # VCOMPREF (CDS)
        
    mira_xs_api.write_register('VDAC_SET_4', 180) # VS0
    mira_xs_api.write_register('VDAC_SET_5', 180) # BSP_REF
    mira_xs_api.write_register('VDAC_SET_3', 180) # VR0
    
    mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 0) #NMOS BUF ACTIVATION
    mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 0) #PMOS BUF ACTIVATION

    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 8) # 7 or 8, for rampgen_vref & rampgen_vramp
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 7)# 5 or 6 and 7, for VR0, VS0 and VBSP
    
    #for vdac_val in range(0, 255, 8):
     #   mira_xs_api.write_register('VDAC_SET_0', vdac_val) # VRAMPREF
      #  mira_xs_api.write_register('VDAC_SET_3', vdac_val) # VR0
       # time.sleep(3) #wait 3 sec

    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_colload(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_colload_constant.txt")
    #util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_cur_starv.txt")

    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'default'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 1) #FOR TEST_MODE SHOULD BE DISABLED
    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit
    mira_xs_api.write_register('IDAC_SET_8', 15) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis
    
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) # col<608>
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 12) # colload_logic_biasn
    
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_colclamp(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_colload_constant.txt")
    #util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_cur_starv.txt")

    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)
    # Manual tweaking
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN    
    mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    
    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit
    mira_xs_api.write_register('IDAC_SET_8', 15) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis
    
    mira_xs_api.write_register('VDAC_SET_3', 199) # VR0
    mira_xs_api.write_register('VDAC_SET_4', 199) # VS0
    
    mira_xs_api.write_register('VDAC_SET_0', 231) # VRAMPREF
    mira_xs_api.write_register('VDAC_SET_1', 225) # VCOMPREF (CDS)
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)
       
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) # col<608>
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 5) # coltest_VR0
    time.sleep(5)
    mira_xs_api.write_register('AMUX2_SEL', 6) # coltest_VS0
    time.sleep(5)
    mira_xs_api.write_register('AMUX2_SEL', 15) # vramp

    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_colbsp(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_bsp.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN    
    mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    
    mira_xs_api.write_register('BSP_COMP_EN', 1) 
    mira_xs_api.write_register('IDAC_SET_4', 15) # active bias current circuit
    mira_xs_api.write_register('IDAC_SET_3', 25) # BSP Comp
    
    mira_xs_api.write_register('VDAC_SET_3', 255) # VR0-> To test BSP funcationality this-VGS should go below BSP_REF
    mira_xs_api.write_register('VDAC_SET_4', 235) # VS0
    mira_xs_api.write_register('VDAC_SET_5', 180) # BSP_REF
    
    mira_xs_api.write_register('AMUX_EN', 1)
    #mira_xs_api.write_register('AMUX_SEL', 11) # BSP_BIASN
    mira_xs_api.write_register('AMUX_SEL', 5) # COL<608>
    
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 7) # BSP_VREF
    time.sleep(5)
    mira_xs_api.write_register('AMUX2_SEL', 5) # VR0
    time.sleep(5)
    mira_xs_api.write_register('AMUX2_SEL', 6) # VS0
    time.sleep(3)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP


    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_coladcana(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_colload_constant.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 15)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 15)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN    
    mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    mira_xs_api.write_register('VDAC_SET_3', 200) # VR0
    mira_xs_api.write_register('VDAC_SET_4', 180) # VS0

    mira_xs_api.write_register('IDAC_SET_0', 15) # comp
    mira_xs_api.write_register('IDAC_SET_1', 15) # KBC
    mira_xs_api.write_register('IDAC_SET_2', 15) # bias_current buffer circuitry

    mira_xs_api.write_register('IDAC_SET_5', 15) # rmp_voltage_buf(shared for ramp & CDS)
    mira_xs_api.write_register('IDAC_SET_6', 15) # bias current buffer circuitry
    mira_xs_api.write_register('IDAC_SET_15', 15)# rampgen IREF (bias block)
    
    mira_xs_api.write_register('RAMP_VREF_EN', 1)
    mira_xs_api.write_register('ADCANA_BIAS_BUF_EN', 1)
    mira_xs_api.write_register('COMP_KBC_EN', 1)
    mira_xs_api.write_register('EN_CLK_RG', 1)    # Enable of Ramp Generation clock
    mira_xs_api.write_register('BIAS_RG_EN', 0)   # Enable ramp generator reference

    mira_xs_api.write_register('COMP_SEL_BW', 15)
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 37)
    mira_xs_api.write_register('BIAS_RG_DIV', 0)  # Binary clock divider inside ramp generator. (0: /1) | (1: /2) | (2-3: /4) 
    mira_xs_api.write_register('BIAS_RG_MULT', 3) #  (0: 1x) | (1: 2x) | (2: 4x) | (3: 8x)

    mira_xs_api.write_register('VDAC_SET_0', 231) # VRAMPREF
    mira_xs_api.write_register('VDAC_SET_1', 216) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 9)  # COMP_BIASN
    #mira_xs_api.write_register('AMUX_SEL', 10) # KBC_BIASN
    #mira_xs_api.write_register('AMUX_SEL', 5) # COL<608>

    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 2) # COMP_OUT
    #mira_xs_api.write_register('AMUX2_SEL', 15)# RAMPGEN_RAMP

    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)
    input('press any key to continue')

def test_coladcdig_mem2(mira_xs_api: MiraXS_API):
    bus = {'axi_offset': 0x70000,
           'axi_read': mira_xs_api.val_api.AxiRead,
           'axi_write': mira_xs_api.val_api.AxiWrite,
           'type': 'axi'}
    regbus = GenericBus(bus_definition=bus, prefix='axi_')
    simple_sensor_ctrl_intf = SimpleSensorCtrlIntf(regbus)

    # Make REQ_EXP and REQ_FRAME low
    simple_sensor_ctrl_intf.initialize_sensor_timing()

    # Functional (User Guide) settings
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0

    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 38
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("util/wgen/mira_xs_timing.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'default'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL

    # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)

    mira_xs_api.goto_idle_state()        # will configure mipi, ctrl_mode, time_bases ..
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    # Increase the number of frames produced by the sensor after each trigger to
    # increase the change of a correctly grabbed image. This is changed by directly
    # writing the register, such that the Grab function will still only ask for 1
    # image from the Deltatec system
    mira_xs_api.write_register('RW_CONTEXT', 0)
    mira_xs_api.write_register('NROF_FRAMES', 2)

    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)
    # Manual tweaking

    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")

    # -----------
    # MEM2 test
    # -----------
    mira_xs_api.write_register('MEM2_TEST_EN', 1) # BYPASSING COL-LOGIC
    mira_xs_api.write_register('MEM2_TEST_DATA', 0) # DATA-INPUT INTO MEM2
    mira_xs_api.write_register('MEM2_TEST_MODE', 1)
    
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()

            print(f'nrof images = {len(images)}')
            print(images[0].pixel_data[0])

            UtilImages.display_images(images)
            # UtilImages.save_image_as_png(images[0], 'sample_scripts/deltatec_digital_test_image')
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                               '  q: quit\n'
                               '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")

def test_coladcdig_logic(mira_xs_api: MiraXS_API):
    # Test starts here with sensor in Supply Off State

    # Functional (User Guide) settings
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 16
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1
    mira_xs_api.pll_params.clk_in = 38.4
    mira_xs_api.time_bases_params.time_unit = 38
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_logic.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'default'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    mira_xs_api.goto_idle_state()       # Will configure mipi, ctrl_mode, time_bases ..
    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    # -----------
    # LOGIC test
    # -----------
    mira_xs_api.write_register('FA_TEST_EN_R', 1) #Apply known data to R input of ADCDIG full adder (test data set with MEM_TEST_R)
    mira_xs_api.write_register('FA_TEST_EN_F', 1) #Apply known data to F input of ADCDIG full adder (test data set with MEM_TEST_F)
    mira_xs_api.write_register('FA_TEST_EN_P', 1) #Apply known data to PREV input of ADCDIG full adder (test data set with MEM_TEST_P)
    mira_xs_api.write_register('MEM_TEST_R', 8191)#Data to be applied as bypass for RE counter, set directly as input to the full adder (when FA_TEST_EN_R = 1). Highest index is PTC bit
    mira_xs_api.write_register('MEM_TEST_F', 8191)#Data to be applied as bypass for FE counter, set directly as input to the full adder (when FA_TEST_EN_F = 1). Highest index is  PTC bit
    mira_xs_api.write_register('MEM_TEST_P', 8191)#Data to be applied as bypass for MEM2 PREV data, set directly as input to the full adder (when FA_TEST_EN_P = 1). Highest index is  PTC bit
    
    
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 1)
    mira_xs_api.write_register('CMD_REQ_1_MASTER', 0)

    #mira_xs_api.start_img_acquisition() # Will give REQ_EXP command to sensor
    #images = mira_xs_api.get_images(n=1)
    #img_helper = UtilImages(images)
    #img_helper.display(1)

def test_coladcdig_mem1(mira_xs_api: MiraXS_API):
    # Functional (User Guide) settings
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0

    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_mem1.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'default'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL

    # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)

    mira_xs_api.goto_idle_state()        # will configure mipi, ctrl_mode, time_bases ..
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    # -----------
    # MEM1 test
    # -----------
    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('VDAC_SET_0', 222) # VRAMPREF [237]
    mira_xs_api.write_register('VDAC_SET_1', 218) # VCOMPREF (CDS)[233]

    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)
    mira_xs_api.write_register('MEM1_TEST_EN', 1) #Enable bypass of comparator output with signal TEST_COMP signal from word generator
    
    mira_xs_api.write_register('LUT_DEL_000', 22) #delay (R_RMPPC_RESET->comp_toggle)
    mira_xs_api.write_register('LUT_DEL_004', 22) #delay (comp_toggle->F_RMPPC_RESET)
    
    for i in range(19,135,10):
        mira_xs_api.write_register('LUT_DEL_002', i) #delay (R_RMPPC_SIG->comp_toggle)
        mira_xs_api.write_register('LUT_DEL_003', 116-(i-19)) #delay (comp_toggle->F_RMPPC_SIG)
     
        keyboard_input = ''
        while keyboard_input != 'q':
            mira_xs_api.start_image_acquisition()

            try:
                images = mira_xs_api.get_images()
                print(f'nrof images = {len(images)}')
                print(images[0].pixel_data[0])
                ###########
                ## NOISE ##
                ###########
                np_image =images[0].pixel_data
                #stdev = np.std(np_image[3:,:], axis=0)
                stdev = np.std(np_image[:,:], axis=0)
                #print(stdev.shape)
                #print(stdev)
                avg = np.mean(stdev)
                noise = avg * 0.528
                print('noise in dn is')
                print(avg)
                print('multiply dn by conversion gain')
                print(noise)
                

                UtilImages.display_images(images)
                # UtilImages.save_image_as_png(images[0], 'sample_scripts/deltatec_digital_test_image')
            except Exception:
                traceback.print_exc()

            keyboard_input = input('Choose an option to continue: \n'
                                '  q: quit\n'
                                '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
            print(f"Your input was: {keyboard_input}")

def test_full_readout_cur_starv(mira_xs_api: MiraXS_API):
    
    # Functional (User Guide) settings
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0

    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_current_starved.txt")

    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    #switch to 12 bit-mode
    #initial_upload.add_sequence(get_incremental_upload_12bit())
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)
    mira_xs_api.goto_idle_state()        # will configure mipi, ctrl_mode, time_bases ..
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    #####################################################################
    ####################FORCURRENTSTARVEDMODEONLY########################
    #####################################################################
    mira_xs_api.write_register('PTR_ANACOL', 42) # ANACOL_TEST WGEN  (41for constant mode) 
    ##################################################################### 
    mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0)
    
    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit
    mira_xs_api.write_register('IDAC_SET_8', 3) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 170) # VS0[220]

    mira_xs_api.write_register('VDAC_SET_0', 202) # VRAMPREF [237]
    mira_xs_api.write_register('VDAC_SET_1', 198) # VCOMPREF (CDS)[233]
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)
    mira_xs_api.write_register('BIAS_RG_MULT', 3)
    mira_xs_api.write_register('BIAS_RG_DIV', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

       
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) # col<608>
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    ##########################################################
    ##########ONLY WHEN CHOOSING CURRENT STARVED MODE#########
    ##########################################################
    mira_xs_api.write_register('ADC_CYC_PAUSE', 804)
    ##########################################################
    ##########################################################
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    #12bit mode
    #mira_xs_api.write_register('ROW_LENGTH', 2000)

    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            print(f'nrof images = {len(images)}')
            print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########
            
            CG = 528 # conversioni gain in uV/DN
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            #print(stdev.shape)
            #print(stdev)
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()
            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG
 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            print('noise in dn is')
            print(avg)
            print('multiply dn by conversion gain')
            print(noise)
            print('row noise is:')
            print(row_noise)
            print('col fpn is:')
            print(col_fpn)

            UtilImages.display_images(images)
            #UtilImages.save_images_as_png(images[0], 'testcases_analog/images/White_BW07_AC4uA_morecds')
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    initial_upload = get_default_initial_upload()   
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)    
    #initial_upload.add_sequence(get_incremental_upload_12bit()) #switch to 12bit or 8bit-mode
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    #util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)
    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 0) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 167) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 162) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 0) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 3)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 60)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)   #[8bit & 10bit=37; 12bit=21]
    #mira_xs_api.write_register('BIAS_RG_MULT', 2)      #[10bit & 8bit=3; 12bit=2]
    #mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=2]

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) # col<608>
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    
    #-------------------------------------------------------------------
    # Row length should be decided based on 12bit, 10bit or 8bit mode
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('ROW_LENGTH', 750) 
    
    for ps in ['VDD28', 'VDD12', 'VDD18']:
        print('current continuos')
        print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
            CG = 528 # conversioni gain in uV/DN 
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            #print(stdev.shape)
            #print(stdev)
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')

            UtilImages.display_images(images)
            #UtilImages.save_image_as_png(images[0], 'testcases_analog/images/TEST_inputground_Sample2_RGMULT2')
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_temp_sensor(mira_xs_api: MiraXS_API):
    
    # Functional (User Guide) settings
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0

    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479
    
    # -------------------------------------------------------------------------
    initial_upload = get_default_initial_upload()
    

    # Modify WGEN program
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_tempsensor.txt")

    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)
    #switch to 12 bit-mode
    initial_upload.add_sequence(get_incremental_upload_12bit())

    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 12
    
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)
    mira_xs_api.goto_idle_state()        # will configure mipi, ctrl_mode, time_bases ..
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    # -------------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 0)

    # Manual tweaking
    
    
    mira_xs_api.write_register('FORCE_YADDR', 1) #EN FAKE ROW
    mira_xs_api.write_register('EXT_YADDR', 1023)#EN FAKE ROW
    # TRIMMING THE SUPPLIES
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    mira_xs_api.write_register('COLDUM_EN', 1)
    mira_xs_api.write_register('TSENS_EN', 1)


    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS LAYER COLLOAD EN
    #mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) #FOR TEST_MODE SHOULD BE DISABLED
    #mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COL_TEST_EN', 1) # Force known voltages on the column bus
    
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0)

    #mira_xs_api.write_register('IDAC_SET_0', 11) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias


    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis
    
    mira_xs_api.write_register('IDAC_SET_10', 15) # tempsens
    
    mira_xs_api.write_register('VDAC_SET_3', 225) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 0) # VS0[220]

    mira_xs_api.write_register('VDAC_SET_0', 202) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 198) # VCOMPREF (CDS)[233]
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 3)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 60)

    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    #mira_xs_api.write_register('BIAS_RG_ADCGAIN', 63)
    #mira_xs_api.write_register('BIAS_RG_MULT', 1)
    #mira_xs_api.write_register('BIAS_RG_DIV', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)
       
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 7) # col<608>
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP

    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    #12bit mode
    mira_xs_api.write_register('ROW_LENGTH', 2000)

    #TEMP CONVERSION
    mira_xs_api.write_register('COLDUM_EN', 1)
    mira_xs_api.write_register('TSENS_EN', 1)
    #mira_xs_api.write_register('PWR_GRPS_TSENS_EN', 0)
    #input('is there any ramp?')
    for i in range(30):
        mira_xs_api.write_register('CMD_TSENS', 1)
        mira_xs_api.write_register('CMD_TSENS', 0)    
        mira_xs_api.write_register('TSENS_HOLD', 1)
        rawtemp = mira_xs_api.read_register('TSENS_VALUE_MASTER')
        mira_xs_api.write_register('TSENS_HOLD', 0)
        temp = rawtemp - 1448
        print('Temp(K) is=')
        print(temp)
        time.sleep(1)

    '''
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            print(f'nrof images = {len(images)}')
            print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            #print(stdev.shape)
            print(stdev)
            avg = 0
            counter = 0
            #for x in stdev:
                #if 0.5<x and x<2:
                    #avg = avg + x
                    #counter = counter + 1
                    #ournoise = avg/counter
    
            avg = np.mean(stdev)
            noise = avg * 0.133
            print('noise in dn is')
            print(avg)
            print('multiply dn by conversion gain')
            print(noise)
            #TEMPSENSOR
            rawtemp = mira_xs_api.read_register('TSENS_VALUE_MASTER')
            temp = rawtemp - 1448
            print('Temp(K) is=')
            print(temp)

            UtilImages.display_images(images)
            #UtilImages.save_image_as_png(images[0], 'testcases_analog/images/TEST_inputground_Sample2_RGMULT2')
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
    '''
def test_full_readout_sandbox(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 5000
    mira_xs_api.black_level_params.black_level = 0

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 640
    mira_xs_api.xroi_params.xwin_right['A'] = 479

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    initial_upload = get_default_initial_upload()   
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)    
    #initial_upload.add_sequence(get_incremental_upload_12bit()) #switch to 12bit or 8bit-mode
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    #util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)
    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 0) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 3) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 183) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 200) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    # 10 bit but with 12 bit settings
    mira_xs_api.write_register('CLKGEN_ADC_DIV', 2) #DIVIDE ADC CLK BY 4 (12bit 10bit 8bit mode)
    mira_xs_api.write_register('LUT_DEL_000', 179)
    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 255)
    mira_xs_api.write_register('LUT_DEL_003', 29)
    # In case extra clk after ramp_pc was also needed +-50 should be applied:
    mira_xs_api.write_register('ADC_CYC_ACT1', 234) # 184 +50
    mira_xs_api.write_register('ADC_CYC_PAUSE', 102) #152 -50
    mira_xs_api.write_register('ADC_CYC_ACT2', 602) # 552 +50

    '''
    # Continue the CLK after ramp_pc to cover delay 10bit/12bit/8bit
    mira_xs_api.write_register('ADC_CYC_ACT1', 384) # 184 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 308)# 608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 752) # 552 +50*4
    '''
    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 21)   #[8bit & 10bit=37; 12bit=21]
    mira_xs_api.write_register('BIAS_RG_MULT', 2)      #[10bit & 8bit=3; 12bit=2]
    mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=2]

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    
    #-------------------------------------------------------------------
    # Row length should be decided based on 12bit, 10bit or 8bit mode
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 1145) #1145 #750 

    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
    '''
    #mira_xs_api.write_register('TEST_LVDS', 2) #Gradient image    
    #mira_xs_api.start_image_acquisition()
    cc_vdd12=[0]*999
    cc_vdd18=[0]*999
    cc_vdd28=[0]*999
    for cs in range(0, 999 ):
        time.sleep(0.00001)
        cc_vdd12[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD12')*1000))
        cc_vdd28[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD28')*1000))
        cc_vdd18[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD18')*1000))
    average_vdd12=np.mean(cc_vdd12)
    average_vdd18=np.mean(cc_vdd18)
    average_vdd28=np.mean(cc_vdd28)
    print('average current vdd12=', average_vdd12)
    print('average current vdd18=', average_vdd18)
    print('average current vdd28=', average_vdd28)
 
    plt.plot(cc_vdd18)
    plt.title("current vdd18")
    plt.xlabel("time")
    plt.ylabel("mA")
    #plt.show()
            
    plt.plot(cc_vdd12)
    plt.title("current vdd12")
    plt.xlabel("time")
    plt.ylabel("mA")
    #plt.show()
 
    plt.plot(cc_vdd28)
    plt.title("current vdd28")
    plt.xlabel("time")
    plt.ylabel("mA")
    #plt.show()
    input('press any key to disable adcdig')  
    mira_xs_api.write_register('EN_CLK_ADC', 0)
    mira_xs_api.write_register('COL60_EN', 0) 
    mira_xs_api.write_register('MEM1_ENABLE', 15)
    
    cc_vdd12=[0]*999
    cc_vdd18=[0]*999
    cc_vdd28=[0]*999
    for cs in range(0, 999 ):
        time.sleep(0.00001)
        cc_vdd12[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD12')*1000))
        cc_vdd28[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD28')*1000))
        cc_vdd18[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD18')*1000))
    average_vdd12=np.mean(cc_vdd12)
    average_vdd18=np.mean(cc_vdd18)
    average_vdd28=np.mean(cc_vdd28)
    print('average current vdd12=', average_vdd12)
    print('average current vdd18=', average_vdd18)
    print('average current vdd28=', average_vdd28)
    
    input('press any key to continue')
    '''
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
            CG = 528 # conversioni gain in uV/DN 12bit 10bit 8bit 
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            images[0].pixel_data = images[0].pixel_data[2:,:]
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[2:640,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            plt.plot(noise_all)
            #plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            UtilImages.display_images(images)
            #UtilImages.save_image_as_png(images[0], 'testcases_analog/images/TEST_inputground_Sample2_RGMULT2')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout_signal_conversion_only(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 5000
    mira_xs_api.black_level_params.black_level = 0

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    initial_upload = get_default_initial_upload()   
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)    
    #initial_upload.add_sequence(get_incremental_upload_12bit()) #switch to 12bit or 8bit-mode
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    #util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)
    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 190) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 240) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    # 10 bit but with 12 bit settings
    mira_xs_api.write_register('CLKGEN_ADC_DIV', 2) #DIVIDE ADC CLK BY 4 (12bit 10bit 8bit mode)
    mira_xs_api.write_register('LUT_DEL_000', 179)
    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 255)
    mira_xs_api.write_register('LUT_DEL_003', 29)
    # In case extra clk after ramp_pc was also needed +-50 should be applied:
    # mira_xs_api.write_register('ADC_CYC_ACT1', 234) # 184 +50
    mira_xs_api.write_register('ADC_CYC_PAUSE', 152) #152 -50
    # mira_xs_api.write_register('ADC_CYC_ACT2', 602) # 552 +50

    '''
    # Continue the CLK after ramp_pc to cover delay 10bit/12bit/8bit
    mira_xs_api.write_register('ADC_CYC_ACT1', 384) # 184 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 308)# 608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 752) # 552 +50*4
    '''
    # bypasses the "MEM2 previous" value with 0 => CDS = SIG - 0
    # mira_xs_api.write_register('MEM_TEST_P', 0)
    # mira_xs_api.write_register('FA_TEST_EN_P', 1)

    # shifting the trigger for digital readout => OUTPUT = RST
    # mira_xs_api.write_register('POS_VIS_TRIGGER', 318)
    # mira_xs_api.write_register('POS_HSYNC_RISE', 342) # +24 of previous case
    

    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 21)   #[8bit & 10bit=37; 12bit=21]
    mira_xs_api.write_register('BIAS_RG_MULT', 2)      #[10bit & 8bit=3; 12bit=2]
    mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=2]

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    
    #-------------------------------------------------------------------
    # Row length should be decided based on 12bit, 10bit or 8bit mode
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 1145) #1145 #750 

    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
 
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition() 

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
            CG = 528 # conversioni gain in uV/DN 12bit 10bit 8bit 
            images[0].pixel_data = images[0].pixel_data[2:,:] # FIRST ROW IS CHOPPED
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            #plt.plot(noise_all)
            #plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            UtilImages.display_images(images)
            #UtilImages.save_image_as_png(images[0], 'testcases_analog/images/TEST_inputground_Sample2_RGMULT2')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout_power_meas(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 0  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 1000000
    mira_xs_api.black_level_params.black_level = 0

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    # mira_xs_api.yroi_params.ysize[0] = 640
    # mira_xs_api.xroi_params.xwin_right['A'] = 479
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    initial_upload = get_default_initial_upload()   
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(wgen_seq)    
    #initial_upload.add_sequence(get_incremental_upload_12bit()) #switch to 12bit or 8bit-mode
    mira_xs_api.initial_upload = initial_upload
    #util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)
    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    # mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    # mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 1) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('EN_AUTO_LPS_TRANS', 1) # effective for non-continious clk 
    # mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    # mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 3) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 193) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 0) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    # 10 bit but with 12 bit settings
    mira_xs_api.write_register('CLKGEN_ADC_DIV', 2) #DIVIDE ADC CLK BY 4 (12bit 10bit 8bit mode)
    mira_xs_api.write_register('LUT_DEL_000', 179)
    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 255)
    mira_xs_api.write_register('LUT_DEL_003', 29)
    # In case extra clk after ramp_pc was also needed +-50 should be applied:
    # mira_xs_api.write_register('ADC_CYC_ACT1', 234) # 184 +50
    mira_xs_api.write_register('ADC_CYC_PAUSE', 152) #152 -50
    # mira_xs_api.write_register('ADC_CYC_ACT2', 602) # 552 +50

    '''
    # Continue the CLK after ramp_pc to cover delay 10bit/12bit/8bit
    mira_xs_api.write_register('ADC_CYC_ACT1', 384) # 184 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 308)# 608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 752) # 552 +50*4
    '''
    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 21)   #[8bit & 10bit=37; 12bit=21]
    mira_xs_api.write_register('BIAS_RG_MULT', 2)      #[10bit & 8bit=3; 12bit=2]
    mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=2]

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 0)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 0)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    
    #-------------------------------------------------------------------
    # Row length should be decided based on 12bit, 10bit or 8bit mode
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 1145) #1145 #750 

    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
    
    #mira_xs_api.write_register('TEST_LVDS', 2) #Gradient image    
    mira_xs_api.start_image_acquisition(bitdepth=10)
    cc_vdd12=[0]*999
    cc_vdd18=[0]*999
    cc_vdd28=[0]*999
    for cs in range(0, 999 ):
        time.sleep(0.001)
        cc_vdd12[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD12')*1000))
        cc_vdd28[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD28')*1000))
        cc_vdd18[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD18')*1000))
    average_vdd12=np.mean(cc_vdd12)
    average_vdd18=np.mean(cc_vdd18)
    average_vdd28=np.mean(cc_vdd28)
    print('average current vdd12=', average_vdd12)
    print('average current vdd18=', average_vdd18)
    print('average current vdd28=', average_vdd28)
 
    plt.plot(cc_vdd18)
    plt.title("current vdd18")
    plt.xlabel("time")
    plt.ylabel("mA")
    #plt.show()
            
    plt.plot(cc_vdd12)
    plt.title("current vdd12")
    plt.xlabel("time")
    plt.ylabel("mA")
    plt.show()
 
    plt.plot(cc_vdd28)
    plt.title("current vdd28")
    plt.xlabel("time")
    plt.ylabel("mA")
    #plt.show()
    # input('press any key to disable adcdig')  
    # mira_xs_api.write_register('EN_CLK_ADC', 0)
    # mira_xs_api.write_register('COL60_EN', 0) 
    # mira_xs_api.write_register('MEM1_ENABLE', 15)
    
    # cc_vdd12=[0]*999
    # cc_vdd18=[0]*999
    # cc_vdd28=[0]*999
    # for cs in range(0, 999 ):
    #     time.sleep(0.00001)
    #     cc_vdd12[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD12')*1000))
    #     cc_vdd28[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD28')*1000))
    #     cc_vdd18[cs]=((mira_xs_api.val_api.GetSupplyCurrent('VDD18')*1000))
    # average_vdd12=np.mean(cc_vdd12)
    # average_vdd18=np.mean(cc_vdd18)
    # average_vdd28=np.mean(cc_vdd28)
    # print('average current vdd12=', average_vdd12)
    # print('average current vdd18=', average_vdd18)
    # print('average current vdd28=', average_vdd28)
    
    input('press any key to continue')

def test_full_readout_10bit(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 20

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    # util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_10bit.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload = get_default_initial_upload()   
    initial_upload.add_sequence(wgen_seq)    
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)

    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 192) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 240) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    #######################
    # 10 bit mode (750MHz)
    #######################
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 39)   #[8bit & 10bit=37; 12bit=21]

    # # GAIN 1 - RST_SWING=200mV - ROWTIME=677
    # CG = 390 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 3)
    
    # mira_xs_api.write_register('LUT_DEL_000', 62)
    # mira_xs_api.write_register('LUT_DEL_001', 0)
    # mira_xs_api.write_register('LUT_DEL_002', 0)
    # mira_xs_api.write_register('LUT_DEL_003', 188)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 256) # 256 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 608) #608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 768) # 768 +50*4

    # mira_xs_api.write_register('OFFSET_CLIPPING', 502)

    # GAIN 2 - RST_SWING=200mV - ROWTIME=805
    CG = 390/2 # conversioni gain in uV/DN
    mira_xs_api.write_register('BIAS_RG_MULT', 2)
    
    mira_xs_api.write_register('LUT_DEL_000', 126)
    mira_xs_api.write_register('LUT_DEL_001', 252)
    mira_xs_api.write_register('LUT_DEL_002', 0)
    mira_xs_api.write_register('LUT_DEL_003', 0)
    mira_xs_api.write_register('ADC_CYC_ACT1', 512)  # 512 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 608) #608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 1024) # 1024 +50*4

    mira_xs_api.write_register('OFFSET_CLIPPING', 1014)

    # # GAIN 4 - RST_SWING=200mV - ROWTIME=1061
    # CG = 390/4 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 1)

    # mira_xs_api.write_register('LUT_DEL_000', 254)
    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 125)
    # mira_xs_api.write_register('LUT_DEL_003', 0)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 1024) # 256 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 608) #608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 1536) # 768 +50*4

    # mira_xs_api.write_register('OFFSET_CLIPPING', 2038)
 
    #############################
    # 10 bit mode half clk speed (375MHz)
    #############################
    # mira_xs_api.write_register('CLKGEN_ADC_DIV', 1)     #divide ADC CLK by 2^x   
    # mira_xs_api.write_register('BIAS_RG_ADCGAIN', 39)   # Adjusting the ramp slope 

    # # GAIN 1 - RST_SWING=200mV - ROWTIME=933
    # CG = 390 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 2)
    # mira_xs_api.write_register('LUT_DEL_000', 126)
    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 125)
    # mira_xs_api.write_register('LUT_DEL_003', 0)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 256)     #256+2*40
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 304)    #244-2*40
    # mira_xs_api.write_register('ADC_CYC_ACT2', 768)     #768+2*40

    # # GAIN 2 - RST_SWING = 200mV - ROWTIME=1189
    # CG = 390/2 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 1)
    # mira_xs_api.write_register('LUT_DEL_000', 254)
    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 253)
    # mira_xs_api.write_register('LUT_DEL_003', 0)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 512)     #512+2*40
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 304)    #304-2*40
    # mira_xs_api.write_register('ADC_CYC_ACT2', 1024)    #1024+2*40    
    
    # # GAIN 4 - RST_SWING = 200mV - ROWTIME= 1701
    # CG = 390/4 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 0)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 1024)     #1024+2*40
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 304)    #304-2*40
    # mira_xs_api.write_register('ADC_CYC_ACT2', 1536)     #1536+2*40
    # mira_xs_api.write_register('LUT_DEL_000', 255)
    # mira_xs_api.write_register('LUT_DEL_004', 254)
    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 255)
    # mira_xs_api.write_register('LUT_DEL_003', 254)

    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 1061)

    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
 
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()
        # ----------------------------------------
        # Measure the power with for loop method
        # ----------------------------------------
        cc_vdd12 = [0] * 99
        cc_vdd18 = [0] * 99
        cc_vdd28 = [0] * 99
        for cs in range(0, 99):
            time.sleep(0.01)
            cc_vdd12[cs] = ((mira_xs_api.val_api.GetSupplyVoltage('VDD12')))
            cc_vdd28[cs] = ((mira_xs_api.val_api.GetSupplyVoltage('VDD28')))
            cc_vdd18[cs] = ((mira_xs_api.val_api.GetSupplyVoltage('VDD18')))
        average_vdd12 = np.mean(cc_vdd12)
        average_vdd18 = np.mean(cc_vdd18)
        average_vdd28 = np.mean(cc_vdd28)
        print('average voltage vdd12=', average_vdd12)
        print('average voltage vdd18=', average_vdd18)
        print('average voltage vdd28=', average_vdd28)

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
             
            images[0].pixel_data = images[0].pixel_data[2:,:] # FIRST ROW IS CHOPPED
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            mean_dn=np.mean(mean_col)
            mean_col_dn=mean_col - mean_dn
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            # plt.plot(noise_all)
            # plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            # plt.plot(mean_col_dn)
            # plt.title("column average")
            # plt.xlabel("column number")
            # plt.ylabel("average in dn")
            # plt.show()
            UtilImages.display_images(images)
            # UtilImages.save_image_as_png(images[0], 'testcases_analog/images/inputgnd_DR1500_RT1000')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout_12bit(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 68

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    # util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_12bit.txt")
    initial_upload = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(get_default_initial_upload())
    initial_upload.add_sequence(get_incremental_upload_12bit())
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 12
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)

    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN   
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 192) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 240) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    #######################
    # 12 bit mode (750MHz)
    #######################
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 23)   #[8bit & 10bit=37; 12bit=21]

    # GAIN 1 - RST_SWING=200mV - ROWTIME=1145
    CG = 138 # conversioni gain in uV/DN
    mira_xs_api.write_register('BIAS_RG_MULT', 2)
    mira_xs_api.write_register('PTR_ANACOL', 45) # ANACOL_TEST WGEN  
    
    mira_xs_api.write_register('LUT_DEL_000', 177)
    mira_xs_api.write_register('LUT_DEL_004', 0)
    mira_xs_api.write_register('LUT_DEL_005', 0)

    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 255)
    mira_xs_api.write_register('LUT_DEL_003', 27)
    mira_xs_api.write_register('LUT_DEL_006', 0)
    mira_xs_api.write_register('LUT_DEL_007', 0)

    mira_xs_api.write_register('ADC_CYC_ACT1', 724) # 724 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 608) #608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 2172) # 2172 +50*4

    mira_xs_api.write_register('OFFSET_CLIPPING', 1414)

    # # GAIN 2 - RST_SWING=200mV - ROWTIME=1507
    # CG = 138/2 # conversioni gain in uV/DN
    # mira_xs_api.write_register('PTR_ANACOL', 45) # ANACOL_TEST WGEN  
    # mira_xs_api.write_register('BIAS_RG_MULT', 1)
    
    # mira_xs_api.write_register('LUT_DEL_000', 255)    
    # mira_xs_api.write_register('LUT_DEL_004', 103)
    # mira_xs_api.write_register('LUT_DEL_005', 0)
    
    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 255)
    # mira_xs_api.write_register('LUT_DEL_003', 208)
    # mira_xs_api.write_register('LUT_DEL_006', 0)
    # mira_xs_api.write_register('LUT_DEL_007', 0)

    # mira_xs_api.write_register('ADC_CYC_ACT1', 1448) # 1148 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 608) # 608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 2896) # 2896 +50*4

    # mira_xs_api.write_register('OFFSET_CLIPPING', 2862)


    # # GAIN 4 - RST_SWING=200mV - ROWTIME=2231 [NOT DONE YET]
    # CG = 138/4 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 0)
    # mira_xs_api.write_register('PTR_ANACOL', 45) # ANACOL_TEST WGEN  

    # mira_xs_api.write_register('LUT_DEL_000', 255)
    # mira_xs_api.write_register('LUT_DEL_004', 255)
    # mira_xs_api.write_register('LUT_DEL_005', 210)

    # mira_xs_api.write_register('LUT_DEL_001', 255)
    # mira_xs_api.write_register('LUT_DEL_002', 255)
    # mira_xs_api.write_register('LUT_DEL_003', 255)
    # mira_xs_api.write_register('LUT_DEL_006', 255)
    # mira_xs_api.write_register('LUT_DEL_007', 60)

    # mira_xs_api.write_register('ADC_CYC_ACT1', 2896) # 256 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 608) #608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 4344) # 768 +50*4

    # mira_xs_api.write_register('OFFSET_CLIPPING', 5772)

    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    #-----------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 2231)

    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
 
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
             
            images[0].pixel_data = images[0].pixel_data[2:,:] # FIRST ROW IS CHOPPED
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            mean_dn=np.mean(mean_col)
            mean_col_dn=mean_col - mean_dn
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            # plt.plot(noise_all)
            # plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            # plt.plot(mean_col_dn)
            # plt.title("column average")
            # plt.xlabel("column number")
            # plt.ylabel("average in dn")
            # plt.show()
            UtilImages.display_images(images)
            # UtilImages.save_image_as_png(images[0], 'testcases_analog/images/inputgnd_DR1500_RT1000')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout_8bit(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 20

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
     # util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_try_to_opt.txt")
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_8bit.txt")
    initial_upload = util_wgen.generate_programming_sequence()
    initial_upload.add_sequence(get_default_initial_upload())
    initial_upload.add_sequence(get_incremental_upload_8bit())
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 8
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)

    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    #mira_xs_api.write_register('IDAC_SET_0', 23) # comp bias
    #mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 31) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 200) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 192) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 240) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    #######################
    # 8 bit mode (750MHz/4)
    #######################
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 39)   #[8bit & 10bit=37; 12bit=21]
    mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=0]

    # # GAIN 1 - RST_SWING=200mV - ROWTIME=677
    # CG = 1562.5 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 3)
    
    # mira_xs_api.write_register('LUT_DEL_000', 62)
    # mira_xs_api.write_register('LUT_DEL_001', 0)
    # mira_xs_api.write_register('LUT_DEL_002', 0)
    # mira_xs_api.write_register('LUT_DEL_003', 188)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 64) # 256 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 152) #608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 192) # 768 +50*4

    #mira_xs_api.write_register('OFFSET_CLIPPING', 118)

    # # GAIN 2 - RST_SWING=200mV - ROWTIME=805
    # CG = 1562.5/2 # conversioni gain in uV/DN
    # mira_xs_api.write_register('BIAS_RG_MULT', 2)
    
    # mira_xs_api.write_register('LUT_DEL_000', 126)
    # mira_xs_api.write_register('LUT_DEL_001', 252)
    # mira_xs_api.write_register('LUT_DEL_002', 0)
    # mira_xs_api.write_register('LUT_DEL_003', 0)
    # mira_xs_api.write_register('ADC_CYC_ACT1', 128)  # 512 +50*4
    # mira_xs_api.write_register('ADC_CYC_PAUSE', 152) #608 -50*4
    # mira_xs_api.write_register('ADC_CYC_ACT2', 256) # 1024 +50*4

    # mira_xs_api.write_register('OFFSET_CLIPPING', 246)

    # # GAIN 4 - RST_SWING=200mV - ROWTIME=1061
    CG = 1562.5/4 # conversioni gain in uV/DN
    mira_xs_api.write_register('BIAS_RG_MULT', 1)

    mira_xs_api.write_register('LUT_DEL_000', 254)
    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 125)
    mira_xs_api.write_register('LUT_DEL_003', 0)
    mira_xs_api.write_register('ADC_CYC_ACT1', 256) # 256 +50*4
    mira_xs_api.write_register('ADC_CYC_PAUSE', 152) #608 -50*4
    mira_xs_api.write_register('ADC_CYC_ACT2', 384) # 768 +50*4

    mira_xs_api.write_register('OFFSET_CLIPPING', 502)

    #mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 7) #COMP_VREF
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ROW_LENGTH', 1062)
       
    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
 
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition()

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
             
            images[0].pixel_data = images[0].pixel_data[2:,:] # FIRST ROW IS CHOPPED
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            mean_dn=np.mean(mean_col)
            mean_col_dn=mean_col - mean_dn
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            # plt.plot(noise_all)
            # plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            # plt.plot(mean_col_dn)
            # plt.title("column average")
            # plt.xlabel("column number")
            # plt.ylabel("average in dn")
            # plt.show()
            UtilImages.display_images(images)
            # UtilImages.save_image_as_png(images[0], 'testcases_analog/images/inputgnd_DR1500_RT1000')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")
def test_full_readout_10bit_bypass_cds(mira_xs_api: MiraXS_API):
    #-------------------------------------------------------------------
    # Set external supplies
    #-------------------------------------------------------------------
    mira_xs_api.default_VDD12 = 1.15
    mira_xs_api.default_VDD18 = 1.8
    mira_xs_api.default_VDD28 = 2.8

    #-------------------------------------------------------------------
    # Functional (User Guide) settings
    #-------------------------------------------------------------------
    mira_xs_api.pll_params.clk_in = 24
    mira_xs_api.pll_params.n = 2
    mira_xs_api.pll_params.target_data_rate = 1500.0
    mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.TRIG_INT
    #mira_xs_api.sensor_ctrl_mode_params.ctrl_mode = SensorControlMode.STREAM
    mira_xs_api.exposure_time_params.nrof_frames['A'] = 1
    mira_xs_api.mipi_functional_params.clock_lane_mode = 1  # continuous clock
    mira_xs_api.time_bases_params.time_unit = 24
    mira_xs_api.frame_rate_params.target_frame_time['A'] = 100000
    mira_xs_api.black_level_params.black_level = 0

    #-------------------------------------------------------------------
    # ROI Settings
    #-------------------------------------------------------------------
    mira_xs_api.yroi_params.ysize[0] = 800
    mira_xs_api.xroi_params.xwin_right['A'] = 599

    #-------------------------------------------------------------------
    # Initial uploads/wgen uploads/bit-mode settings/...
    #-------------------------------------------------------------------
    util_wgen = UtilWgen("testcases_analog/wgen_debug/mira_xs_timing_full_readout_bypass_cds.txt")
    wgen_seq = util_wgen.generate_programming_sequence()
    initial_upload = get_default_initial_upload()   
    initial_upload.add_sequence(wgen_seq)    
    mira_xs_api.sensor_operating_mode.upload_seq = initial_upload
    mira_xs_api.sensor_operating_mode.bitmode = 10
    util_wgen.wgen_parser.generate_wavedrom({'anacol' : 'coltest'}, CreateWgenProg.anacol_signals)     # Print the wavedrom of the chosen program

    #-------------------------------------------------------------------
    # Going through all states of the sensor & measuring the power
    #-------------------------------------------------------------------
    mira_xs_api.goto_ldo_off_state()    # will do power up sequence
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current LDO off state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
      
    mira_xs_api.goto_hard_reset_state() # Will set LDO_EN high
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current hard reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.goto_soft_reset_state() # Will release hard reset, upload initial_upload and PLL
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current soft reset state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.write_register('DPHY_VCAL_HSTX_SEL', 1)       # Get trimming values from register as OTP is not programmed
    mira_xs_api.write_register('DPHY_CAL_TX_RCAL_SEL', 1)     # Get trimming values from register as OTP is not programmed
  
    mira_xs_api.goto_idle_state()       # will configure mipi, ctrl_mode, time_bases ..
    #for ps in ['VDD28', 'VDD12', 'VDD18']:
        #print('current idle state')
        #print(f"PS {ps} : {mira_xs_api.val_api.GetSupplyVoltage(ps)} V, {mira_xs_api.val_api.GetSupplyCurrent(ps)*1000} mA")
   
    mira_xs_api.upload_context('A')
    mira_xs_api.upload_yroi()

    #-------------------------------------------------------------------
    # Power optimiztion on/off
    #-------------------------------------------------------------------
    mira_xs_api.write_register('EN_POWER_OPT', 1)
    
    #-------------------------------------------------------------------
    # Trimming the LDOs
    #-------------------------------------------------------------------
    #mira_xs_api.write_register('VDDANA_EN', 0) #ENABLE VDDANA
    #input('this is the time to enable power supply')
    mira_xs_api.write_register('VDDANA_TRIMM_SEL', 1) # 0->OTP
    mira_xs_api.write_register('VDDANA_TRIMM_VAL', 10)
    mira_xs_api.write_register('VDDPIX_TRIMM_SEL', 1)
    mira_xs_api.write_register('VDDPIX_TRIMM_VAL', 10)
    mira_xs_api.write_register('VSSPC_TRIMM_SEL', 1)
    mira_xs_api.write_register('VSSPC_TRIMM_VAL', 15) 
    mira_xs_api.write_register('CP_TRIMM_SEL', 1)
    mira_xs_api.write_register('CP_TRIMM_VAL', 4)

    #-------------------------------------------------------------------
    # Test mode settings of the logic layer only   
    #------------------------------------------------------------------- 
    mira_xs_api.write_register('FORCE_YADDR', 1) # Enabling the fake row for test mode only
    mira_xs_api.write_register('EXT_YADDR', 1023)
    mira_xs_api.write_register('COL_LOAD_EN', 0) #CIS Layer colload on/off
    mira_xs_api.write_register('AUTO_CALC_ROWDR_EN', 0) # for test mode (fake row) should be disabled
    mira_xs_api.write_register('AUTO_CALC_COL60_EN', 1) # Turn on/off analog blocks outside of ROI
    mira_xs_api.write_register('COL_TEST_EN', 1) # coltest on/off
    mira_xs_api.write_register('PTR_ANACOL', 41) # ANACOL_TEST WGEN  (41for constant mode) 
    #mira_xs_api.write_register('COLCLAMP_EN_EVEN', 0) #Enable column clamp on even columns. Used during coltest where it needs to be deactivated to detect shorts between columns
    mira_xs_api.write_register('BSP_COMP_EN', 0) # BSP on/off

    #-------------------------------------------------------------------
    # Bias settings [LUT available above]
    #-------------------------------------------------------------------    
    # mira_xs_api.write_register('IDAC_SET_0', 15) # comp bias
    # mira_xs_api.write_register('IDAC_SET_1', 15) # comp kbc bias
    # mira_xs_api.write_register('IDAC_SET_2', 31) # comp & kbc buffer bias

    mira_xs_api.write_register('IDAC_SET_5', 7) # ramp and cds buffer bias
    #mira_xs_api.write_register('IDAC_SET_19', 31) #bias of vdac for vramp_ref_buffer

    mira_xs_api.write_register('IDAC_SET_7', 15) # active bias current circuit colload
    mira_xs_api.write_register('IDAC_SET_8', 3) # colload_logic
    mira_xs_api.write_register('IDAC_SET_9', 15) # colload_cis

    #-------------------------------------------------------------------
    # Voltage references 
    #-------------------------------------------------------------------
    mira_xs_api.write_register('VDAC_SET_0', 159) # VRAMPREF [237][202=1.72V][167=1.42V]
    mira_xs_api.write_register('VDAC_SET_1', 155) # VCOMPREF (CDS)
    
    mira_xs_api.write_register('VDAC_SET_3', 0) # VR0[225]
    mira_xs_api.write_register('VDAC_SET_4', 240) # VS0[220]

    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFP', 2)
    #mira_xs_api.write_register('BIAS_VDAC_EN_BUFN', 61)

    #-------------------------------------------------------------------
    # ADC settings
    #-------------------------------------------------------------------
    mira_xs_api.write_register('ADC_CDS_BYPASS', 1)

    

    #############################
    # 10 bit mode half clk speed
    #############################
    mira_xs_api.write_register('CLKGEN_ADC_DIV', 1)     #divide ADC CLK by 2^x   
    mira_xs_api.write_register('BIAS_RG_ADCGAIN', 39)   # Adjusting the ramp slope 

    # GAIN 1 - RST_SWING=200mV - ROWTIME=933
    CG = 390 # conversioni gain in uV/DN
    mira_xs_api.write_register('ROW_LENGTH', 1000) 
    mira_xs_api.write_register('BIAS_RG_MULT', 2)
    mira_xs_api.write_register('LUT_DEL_000', 126)
    mira_xs_api.write_register('LUT_DEL_001', 255)
    mira_xs_api.write_register('LUT_DEL_002', 125)
    mira_xs_api.write_register('LUT_DEL_003', 0)
    mira_xs_api.write_register('ADC_CYC_ACT1', 256)     #256+2*40
    mira_xs_api.write_register('ADC_CYC_PAUSE', 304)    #244-2*40
    mira_xs_api.write_register('ADC_CYC_ACT2', 768)     #768+2*40

    

    # bypasses the "MEM2 previous" value with 0 => CDS = SIG - 0
    # mira_xs_api.write_register('MEM_TEST_P', 0)
    # mira_xs_api.write_register('FA_TEST_EN_P', 1)

    # shifting the trigger for digital readout => OUTPUT = RST
    # mira_xs_api.write_register('POS_VIS_TRIGGER', 192) # for (i0=62,192) (i0=126,192+(126-62)*5.333/13.333=26 )
    # mira_xs_api.write_register('POS_HSYNC_RISE', 216) # = 192 + 24 of previous case
    
    # mira_xs_api.write_register('COMP_KBC_EN', 0)
    mira_xs_api.write_register('COMP_SEL_BW', 7)

    #mira_xs_api.write_register('BIAS_RG_ADCGAIN', 37)   #[8bit & 10bit=37; 12bit=21]
    # mira_xs_api.write_register('BIAS_RG_MULT', 3)      #[10bit & 8bit=3; 12bit=2]
    # mira_xs_api.write_register('BIAS_RG_DIV', 0)       #[10bit & 12bit=0; 8bit=2]

    #-------------------------------------------------------------------
    # ANAMUX  
    #-------------------------------------------------------------------
    mira_xs_api.write_register('AMUX_EN', 1)
    mira_xs_api.write_register('AMUX_SEL', 5) 
    mira_xs_api.write_register('AMUX2_EN', 1)
    mira_xs_api.write_register('AMUX2_SEL', 15) # VRAMP
    
    #-------------------------------------------------------------------    
    mira_xs_api.write_register('RW_CONTEXT', 0)
    print(f"YWIN0_SIZE_MASTER = {mira_xs_api.read_register('YWIN0_SIZE_MASTER')}")
    print(f"XWIN_RIGHT_MASTER = {mira_xs_api.read_register('XWIN_RIGHT_MASTER')}")
    print(f"XWIN_RIGHT_SLAVE = {mira_xs_api.read_register('XWIN_RIGHT_SLAVE')}")
    
    #-------------------------------------------------------------------
    # Grabbing image/ calculating the noise / Displaying(saving) image
    #-------------------------------------------------------------------
 
    keyboard_input = ''
    while keyboard_input != 'q':
        mira_xs_api.start_image_acquisition() 

        try:
            images = mira_xs_api.get_images()                   
            #print(f'nrof images = {len(images)}')
            #print(images[0].pixel_data[0])
            ###########
            ## NOISE ##
            ###########            
             
            images[0].pixel_data = images[0].pixel_data[2:,:] # FIRST ROW IS CHOPPED
            np_image =images[0].pixel_data
            #stdev = np.std(np_image[3:,:], axis=0)
            stdev = np.std(np_image[:,:], axis=0)
            noise_all=stdev*CG
            avg = np.mean(stdev)
            np_image_t=np_image.transpose()            
            mean_row=np.mean(np_image_t[:,:], axis=0)
            row_noise=np.std(mean_row)*CG 
            mean_col=np.mean(np_image_t[:,:], axis=1)
            mean_dn=np.mean(mean_col)
            mean_col_dn=mean_col - mean_dn
            col_fpn=np.std(mean_col)*CG
            noise = avg * CG
            noise_temporal=math.sqrt(noise**2-row_noise**2)
            print('noise in dn is:', avg)
            print("random noise is:", round(noise),"uV")
            print('row noise is:', round(row_noise),'uV')
            print('col fpn is:', round(col_fpn), 'uV')
            print('temporal noise is:', round(noise_temporal), 'uV')
            #plt.plot(noise_all)
            #plt.show()
            print('noise all cols max', max(noise_all))
            #print('std_col424 is:', noise_all[424])
            #print('max val in col424 is:', max(np_image[:,424]),'and min is:', min(np_image[:,424]))
            # plt.plot(mean_col_dn)
            # plt.title("column average")
            # plt.xlabel("column number")
            # plt.ylabel("average in dn")
            # plt.show()
            UtilImages.display_images(images)
            #UtilImages.save_image_as_png(images[0], 'testcases_analog/images/TEST_inputground_Sample2_RGMULT2')
            
        except Exception:
            traceback.print_exc()

        keyboard_input = input('Choose an option to continue: \n'
                            '  q: quit\n'
                            '  anything else: send REQ_EXP command (sw controlled) to sensor: ')
        print(f"Your input was: {keyboard_input}")