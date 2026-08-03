from __future__ import annotations

NOTICE = "FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION"


def sources() -> dict[str, str]:
    return {
        "00_types.scl": f'''// {NOTICE}
TYPE "E_MachineState"
VERSION : 0.1
   (UNINITIALIZED := 0, INITIALIZING := 10, STOPPED := 20, READY := 30, AUTOMATIC := 40, MANUAL_SETUP := 50, HOLDING := 60, CONTROLLED_STOPPING := 70, FAULTED := 80, RECOVERY_RESET := 90);
END_TYPE

TYPE "E_AutoStep"
VERSION : 0.1
   (WAIT_PAIR := 0, SECURE_PAIR := 10, FILL_PAIR := 20, DRIP_SETTLE := 30, INSPECT := 40, TRANSFER := 50, RELEASE_PAIR := 60);
END_TYPE

TYPE "E_FillDiag"
VERSION : 0.2
   (FILL_OK := 0, INVALID_CONFIG := 1, ANALOG_BROKEN_WIRE := 2, NO_FLOW := 3, PULSE_ANALOG_DISAGREE := 4, FILL_TIMEOUT := 5, UNDERFILL := 6, OVERFILL := 7, VALVE_OPEN_MISMATCH := 8, VALVE_CLOSE_MISMATCH := 9, CONTINUED_FLOW := 10, ABORTED := 11, PULSE_MISSING := 12, ANALOG_NO_FLOW := 13, PULSE_COUNTER_DISCONTINUITY := 14);
END_TYPE

TYPE "E_VisionDiag"
VERSION : 0.3
   (VISION_OK := 0, READY_TIMEOUT := 1, RESULT_TIMEOUT := 2, RESULT_ID_MISMATCH := 3, QUALITY_BLOCK := 4, HEARTBEAT_LOSS := 5, INTERFACE_CONTRADICTION := 6, RESULT_STUCK_VALID := 7, NON_MONOTONIC_REQUEST := 8, SESSION_MISMATCH := 9, MODEL_MISMATCH := 10);
END_TYPE

TYPE "UDT_Recipe"
VERSION : 0.2
   STRUCT
      RecipeId : UInt;
      TargetMlCh1 : Real;
      TargetMlCh2 : Real;
      PulsesPerLitreCh1 : Real;
      PulsesPerLitreCh2 : Real;
      UnderToleranceMl : Real;
      OverToleranceMl : Real;
      NoFlowTimeout : Time;
      FillTimeout : Time;
      ValveOpenTimeout : Time;
      ValveCloseTimeout : Time;
      PlausibilityTime : Time;
      PulseWindowTimeS : Real;
      DripSettleTime : Time;
      VisionTimeout : Time;
      TargetFillLevel : Real;
   END_STRUCT;
END_TYPE

TYPE "UDT_VisionResult"
VERSION : 0.3
   STRUCT
      ResultValid : Bool;
      ResultId : UDInt;
      SessionEpoch : UDInt;
      Bottle1Pass : Bool;
      Bottle2Pass : Bool;
      Fill1Status : USInt;
      Fill2Status : USInt;
      LeakOrSpill : Bool;
      LowConfidence : Bool;
      Warning : Bool;
      Fault : Bool;
      InferenceTimeMs : UDInt;
      Heartbeat : UDInt;
      ModelId : String[32];
      ModelHash : String[64];
   END_STRUCT;
END_TYPE

TYPE "UDT_HmiCommand"
VERSION : 0.1
   STRUCT
      Request : Bool;
      RequestSeq : UDInt;
      AcceptedSeq : UDInt;
      RejectedSeq : UDInt;
      Busy : Bool;
      Allowed : Bool;
      DisabledReason : UInt;
   END_STRUCT;
END_TYPE

TYPE "UDT_DrivePzd"
VERSION : 0.1
   STRUCT
      StatusWord1 : Word;
      ActualSpeedPzd : Int;
      ControlWord1 : Word;
      SpeedSetpointPzd : Int;
      CommsHealthy : Bool;
      Ready : Bool;
      Running : Bool;
      Fault : Bool;
      ActualSpeedPct : Real;
   END_STRUCT;
END_TYPE

TYPE "UDT_CellInputs"
VERSION : 0.1
   STRUCT
      SafetyOk : Bool;
      GuardClosed : Bool;
      AirPressureOk : Bool;
      ProductSupplyOk : Bool;
      Bottle1Present : Bool;
      Bottle2Present : Bool;
      GateOpen : Bool;
      GateClosed : Bool;
      ClampReleased : Bool;
      ClampEngaged : Bool;
      Valve1Closed : Bool;
      Valve2Closed : Bool;
      CapperReady : Bool;
      CapperBusy : Bool;
      CapperComplete : Bool;
      CapperFault : Bool;
      LocalReset : Bool;
      LocalStop : Bool;
      Flow1Raw : Int;
      Flow2Raw : Int;
      Flow1ChannelFault : Bool;
      Flow2ChannelFault : Bool;
      Flow1PulseChannelFault : Bool;
      Flow2PulseChannelFault : Bool;
      PulseTotal1 : UDInt;
      PulseTotal2 : UDInt;
      ConveyorPnHealthy : Bool;
      PumpPnHealthy : Bool;
   END_STRUCT;
END_TYPE

TYPE "UDT_NativeBindings"
VERSION : 0.1
   STRUCT
      ConveyorPnIoValid : Bool;
      PumpPnIoValid : Bool;
      Flow1PulseTotal : UDInt;
      Flow2PulseTotal : UDInt;
      Flow1ChannelFault : Bool;
      Flow2ChannelFault : Bool;
      Flow1PulseChannelFault : Bool;
      Flow2PulseChannelFault : Bool;
   END_STRUCT;
END_TYPE

TYPE "UDT_OutputCommands"
VERSION : 0.1
   STRUCT
      FillValve1 : Bool;
      FillValve2 : Bool;
      GateOpen : Bool;
      GateClose : Bool;
      ClampEngage : Bool;
      ClampRelease : Bool;
      CapperRequest : Bool;
      CameraLight : Bool;
      StackGreen : Bool;
      StackAmber : Bool;
      StackRed : Bool;
      Audible : Bool;
   END_STRUCT;
END_TYPE''',

        "DB_Global.scl": f'''// {NOTICE}
DATA_BLOCK "DB_IO"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Inputs : "UDT_CellInputs";
      Commands : "UDT_OutputCommands";
      ReleasePermissive : Bool;
      PowerRecoveryRequired : Bool;
   END_VAR
BEGIN
END_DATA_BLOCK

DATA_BLOCK "DB_HMI"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Start : "UDT_HmiCommand";
      ControlledStop : "UDT_HmiCommand";
      Reset : "UDT_HmiCommand";
      AlarmAck : "UDT_HmiCommand";
      AutoMode : "UDT_HmiCommand";
      ManualMode : "UDT_HmiCommand";
      DispositionRemoved : "UDT_HmiCommand";
      RecipeApply : "UDT_HmiCommand";
      ManualConveyorJog : "UDT_HmiCommand";
      ManualPumpJog : "UDT_HmiCommand";
      ManualValve1 : "UDT_HmiCommand";
      ManualValve2 : "UDT_HmiCommand";
      ManualSecure : "UDT_HmiCommand";
      CommandHeartbeat : UDInt;
      CommunicationsHealthy : Bool;
      StateCode : UInt;
      AutoStepCode : UInt;
      FirstOutAlarm : UInt;
      QualityHold : Bool;
   END_VAR
BEGIN
END_DATA_BLOCK

DATA_BLOCK "DB_NativeBindings"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Inputs : "UDT_NativeBindings";
   END_VAR
BEGIN
END_DATA_BLOCK

DATA_BLOCK "DB_Recipe"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Candidate : "UDT_Recipe";
      Active : "UDT_Recipe";
      Apply : "UDT_HmiCommand";
   END_VAR
BEGIN
END_DATA_BLOCK

DATA_BLOCK "DB_VisionComms"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Enable : Bool;
      Trigger : Bool;
      InspectionId : UDInt;
      RecipeId : UInt;
      ExpectedBottles : USInt;
      TargetFillLevel : Real;
      PlcHeartbeat : UDInt;
      Ready : Bool;
      Busy : Bool;
      ResultAckId : UDInt;
      DiagReason : "E_VisionDiag";
      Result : "UDT_VisionResult";
   END_VAR
   // Controller/approved-model identity must survive a warm or power restart.
   // A memory reset is a controlled commissioning event and requires the edge
   // replay state to be purged before production is re-enabled.
   VAR RETAIN
      SessionEpoch : UDInt;
      ExpectedModelId : String[32];
      ExpectedModelHash : String[64];
      ModelConfigurationApproved : Bool;
   END_VAR
BEGIN
END_DATA_BLOCK

DATA_BLOCK "DB_Drives"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
   VAR
      Conveyor : "UDT_DrivePzd";
      Pump : "UDT_DrivePzd";
   END_VAR
BEGIN
END_DATA_BLOCK''',

        "FB_HMICommandManager.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_HMICommandManager"
VAR_INPUT
   StartRequest : Bool; StartSeq : UDInt; StopRequest : Bool; StopSeq : UDInt;
   ResetRequest : Bool; ResetSeq : UDInt; AckRequest : Bool; AckSeq : UDInt;
   AutoRequest : Bool; AutoSeq : UDInt; ManualRequest : Bool; ManualSeq : UDInt;
   DispositionRequest : Bool; DispositionSeq : UDInt;
   ManualConveyorRequest : Bool; ManualPumpRequest : Bool; ManualValve1Request : Bool; ManualValve2Request : Bool; ManualSecureRequest : Bool; ManualHoldAllowed : Bool;
   LocalStop : Bool; LocalReset : Bool; CommandHeartbeat : UDInt;
   StartAllowed : Bool; ResetAllowed : Bool; AutoAllowed : Bool; ManualAllowed : Bool; DispositionAllowed : Bool;
END_VAR
VAR_OUTPUT
   StartPulse : Bool; StopPulse : Bool; ResetPulse : Bool; AckPulse : Bool;
   AutoPulse : Bool; ManualPulse : Bool; DispositionPulse : Bool; CommunicationsHealthy : Bool;
   ManualConveyorCmd : Bool; ManualPumpCmd : Bool; ManualValve1Cmd : Bool; ManualValve2Cmd : Bool; ManualSecureCmd : Bool;
   StartAcceptedSeq : UDInt; StartRejectedSeq : UDInt; StopAcceptedSeq : UDInt;
   ResetAcceptedSeq : UDInt; ResetRejectedSeq : UDInt; AckAcceptedSeq : UDInt;
   AutoAcceptedSeq : UDInt; AutoRejectedSeq : UDInt; ManualAcceptedSeq : UDInt; ManualRejectedSeq : UDInt;
   DispositionAcceptedSeq : UDInt; DispositionRejectedSeq : UDInt;
END_VAR
VAR
   localResetEdge : R_TRIG;
   lastHeartbeat : UDInt;
   tHeartbeat : TON;
END_VAR
BEGIN
   #StartPulse := FALSE; #StopPulse := FALSE; #ResetPulse := FALSE; #AckPulse := FALSE;
   #AutoPulse := FALSE; #ManualPulse := FALSE; #DispositionPulse := FALSE;
   #localResetEdge(CLK := #LocalReset);
   #tHeartbeat(IN := (#CommandHeartbeat = #lastHeartbeat), PT := T#2s);
   #CommunicationsHealthy := NOT #tHeartbeat.Q;
   #ManualConveyorCmd := #CommunicationsHealthy AND #ManualHoldAllowed AND #ManualConveyorRequest;
   #ManualPumpCmd := #CommunicationsHealthy AND #ManualHoldAllowed AND #ManualPumpRequest;
   #ManualValve1Cmd := #CommunicationsHealthy AND #ManualHoldAllowed AND #ManualValve1Request;
   #ManualValve2Cmd := #CommunicationsHealthy AND #ManualHoldAllowed AND #ManualValve2Request;
   #ManualSecureCmd := #CommunicationsHealthy AND #ManualHoldAllowed AND #ManualSecureRequest;
   #lastHeartbeat := #CommandHeartbeat;
   IF #CommunicationsHealthy AND #StartRequest AND (#StartSeq <> #StartAcceptedSeq) AND (#StartSeq <> #StartRejectedSeq) THEN
      IF #StartAllowed THEN #StartPulse := TRUE; #StartAcceptedSeq := #StartSeq; ELSE #StartRejectedSeq := #StartSeq; END_IF;
   END_IF;
   // Local hardwired commands never consume or reject an HMI sequence number.
   IF #LocalStop THEN #StopPulse := TRUE; END_IF;
   IF #CommunicationsHealthy AND #StopRequest AND (#StopSeq <> #StopAcceptedSeq) THEN #StopPulse := TRUE; #StopAcceptedSeq := #StopSeq; END_IF;
   IF #localResetEdge.Q AND #ResetAllowed THEN #ResetPulse := TRUE; END_IF;
   IF #CommunicationsHealthy AND #ResetRequest AND (#ResetSeq <> #ResetAcceptedSeq) AND (#ResetSeq <> #ResetRejectedSeq) THEN
      IF #ResetAllowed THEN #ResetPulse := TRUE; #ResetAcceptedSeq := #ResetSeq; ELSE #ResetRejectedSeq := #ResetSeq; END_IF;
   END_IF;
   IF #CommunicationsHealthy AND #AckRequest AND (#AckSeq <> #AckAcceptedSeq) THEN #AckPulse := TRUE; #AckAcceptedSeq := #AckSeq; END_IF;
   IF #CommunicationsHealthy AND #AutoRequest AND (#AutoSeq <> #AutoAcceptedSeq) AND (#AutoSeq <> #AutoRejectedSeq) THEN IF #AutoAllowed THEN #AutoPulse := TRUE; #AutoAcceptedSeq := #AutoSeq; ELSE #AutoRejectedSeq := #AutoSeq; END_IF; END_IF;
   IF #CommunicationsHealthy AND #ManualRequest AND (#ManualSeq <> #ManualAcceptedSeq) AND (#ManualSeq <> #ManualRejectedSeq) THEN IF #ManualAllowed THEN #ManualPulse := TRUE; #ManualAcceptedSeq := #ManualSeq; ELSE #ManualRejectedSeq := #ManualSeq; END_IF; END_IF;
   IF #CommunicationsHealthy AND #DispositionRequest AND (#DispositionSeq <> #DispositionAcceptedSeq) AND (#DispositionSeq <> #DispositionRejectedSeq) THEN IF #DispositionAllowed THEN #DispositionPulse := TRUE; #DispositionAcceptedSeq := #DispositionSeq; ELSE #DispositionRejectedSeq := #DispositionSeq; END_IF; END_IF;
END_FUNCTION_BLOCK''',

        "FB_VFD.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_VFD"
VAR_INPUT
   Enable : Bool;
   RunRequest : Bool;
   ResetEdge : Bool;
   CommsHealthy : Bool;
   StatusWord1 : Word;
   ActualSpeedPzd : Int;
   SpeedReferencePct : Real;
   StartTimeout : Time;
   StopTimeout : Time;
END_VAR
VAR_OUTPUT
   ControlWord1 : Word;
   SpeedSetpointPzd : Int;
   Ready : Bool;
   Running : Bool;
   Stopped : Bool;
   Fault : Bool;
   ActualSpeedPct : Real;
   DiagReason : UInt;
END_VAR
VAR
   tStart : TON;
   tStop : TON;
   boundedSpeed : Real;
END_VAR
BEGIN
   #Ready := #CommsHealthy AND ((#StatusWord1 AND W#16#0001) <> W#16#0000);
   #Running := #CommsHealthy AND ((#StatusWord1 AND W#16#0004) <> W#16#0000);
   #Fault := NOT #CommsHealthy OR ((#StatusWord1 AND W#16#0008) <> W#16#0000) OR #Fault;
   #Stopped := NOT #Running AND (ABS(#ActualSpeedPzd) < 164);
   #ActualSpeedPct := INT_TO_REAL(#ActualSpeedPzd) * 100.0 / 16384.0;
   #boundedSpeed := LIMIT(MN := -100.0, IN := #SpeedReferencePct, MX := 100.0);
   #SpeedSetpointPzd := REAL_TO_INT(#boundedSpeed * 16384.0 / 100.0);
   #ControlWord1 := W#16#047E;
   IF #Enable AND #RunRequest AND #Ready AND NOT #Fault THEN #ControlWord1 := W#16#047F; END_IF;
   IF #ResetEdge AND NOT #RunRequest AND #CommsHealthy THEN #ControlWord1 := #ControlWord1 OR W#16#0080; END_IF;
   #tStart(IN := #RunRequest AND #Ready AND NOT #Running, PT := #StartTimeout);
   #tStop(IN := NOT #RunRequest AND NOT #Stopped, PT := #StopTimeout);
   IF NOT #CommsHealthy THEN #DiagReason := 1;
   ELSIF ((#StatusWord1 AND W#16#0008) <> W#16#0000) THEN #DiagReason := 2;
   ELSIF #tStart.Q THEN #Fault := TRUE; #DiagReason := 3;
   ELSIF #tStop.Q THEN #Fault := TRUE; #DiagReason := 4;
   ELSIF NOT #Fault THEN #DiagReason := 0; END_IF;
   IF #ResetEdge AND #CommsHealthy AND NOT #RunRequest AND ((#StatusWord1 AND W#16#0008) = W#16#0000) THEN #Fault := FALSE; #DiagReason := 0; END_IF;
END_FUNCTION_BLOCK''',

        "FB_Actuator2Pos.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_Actuator2Pos"
VAR_INPUT Enable : Bool; CmdToA : Bool; CmdToB : Bool; AtA : Bool; AtB : Bool; ResetEdge : Bool; TravelTime : Time; END_VAR
VAR_OUTPUT OutToA : Bool; OutToB : Bool; InPosition : Bool; Fault : Bool; DiagReason : UInt; END_VAR
VAR tTravel : TON; motion : Bool; END_VAR
BEGIN
   #OutToA := #Enable AND #CmdToA AND NOT #CmdToB AND NOT #Fault;
   #OutToB := #Enable AND #CmdToB AND NOT #CmdToA AND NOT #Fault;
   #motion := (#OutToA AND NOT #AtA) OR (#OutToB AND NOT #AtB);
   #tTravel(IN := #motion, PT := #TravelTime);
   IF #AtA AND #AtB THEN #Fault := TRUE; #DiagReason := 1;
   ELSIF #CmdToA AND #CmdToB THEN #Fault := TRUE; #DiagReason := 2;
   ELSIF #tTravel.Q THEN #Fault := TRUE; #DiagReason := 3; END_IF;
   #InPosition := (#CmdToA AND #AtA AND NOT #AtB) OR (#CmdToB AND #AtB AND NOT #AtA);
   IF #ResetEdge AND NOT (#AtA AND #AtB) AND NOT (#CmdToA OR #CmdToB) THEN #Fault := FALSE; #DiagReason := 0; END_IF;
END_FUNCTION_BLOCK''',

        "FB_RecipeManager.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_RecipeManager"
VAR_INPUT Candidate : "UDT_Recipe"; ApplyRequest : Bool; RequestSeq : UDInt; MachineStopped : Bool; END_VAR
VAR_OUTPUT Active : "UDT_Recipe"; Valid : Bool; Rejected : Bool; AcceptedSeq : UDInt; RejectedSeq : UDInt; END_VAR
BEGIN
   #Valid := (#Candidate.TargetMlCh1 >= 10.0) AND (#Candidate.TargetMlCh1 <= 10000.0)
      AND (#Candidate.TargetMlCh2 >= 10.0) AND (#Candidate.TargetMlCh2 <= 10000.0)
      AND (#Candidate.PulsesPerLitreCh1 >= 1.0) AND (#Candidate.PulsesPerLitreCh1 <= 10000000.0)
      AND (#Candidate.PulsesPerLitreCh2 >= 1.0) AND (#Candidate.PulsesPerLitreCh2 <= 10000000.0)
      AND (#Candidate.UnderToleranceMl >= 0.0) AND (#Candidate.OverToleranceMl >= 0.0)
      AND (#Candidate.NoFlowTimeout >= T#100ms) AND (#Candidate.FillTimeout > #Candidate.NoFlowTimeout)
      AND (#Candidate.ValveOpenTimeout >= T#100ms) AND (#Candidate.ValveCloseTimeout >= T#100ms)
      AND (#Candidate.PlausibilityTime >= T#100ms) AND (#Candidate.PulseWindowTimeS >= 0.1)
      AND (#Candidate.DripSettleTime >= T#100ms) AND (#Candidate.VisionTimeout >= T#100ms)
      AND ((#Candidate.TargetMlCh1 * #Candidate.PulsesPerLitreCh1) >= 1000.0)
      AND ((#Candidate.TargetMlCh2 * #Candidate.PulsesPerLitreCh2) >= 1000.0)
      AND (#Candidate.TargetFillLevel >= 0.1) AND (#Candidate.TargetFillLevel <= 1.0);
   #Rejected := FALSE;
   IF #ApplyRequest AND (#RequestSeq <> #AcceptedSeq) AND (#RequestSeq <> #RejectedSeq) THEN
      IF #MachineStopped AND #Valid THEN #Active := #Candidate; #AcceptedSeq := #RequestSeq;
      ELSE #Rejected := TRUE; #RejectedSeq := #RequestSeq; END_IF;
   END_IF;
END_FUNCTION_BLOCK''',

        "FB_AlarmManager.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_AlarmManager"
VAR_INPUT ActiveFaults : Array[0..31] of Bool; FaultCodes : Array[0..31] of UInt; AckEdge : Bool; ResetEdge : Bool; END_VAR
VAR_OUTPUT AnyFault : Bool; FirstOutCode : UInt; Acknowledged : Bool; END_VAR
VAR i : Int; latched : Bool; END_VAR
BEGIN
   #AnyFault := FALSE;
   FOR #i := 0 TO 31 DO
      #AnyFault := #AnyFault OR #ActiveFaults[#i];
      IF #ActiveFaults[#i] AND NOT #latched THEN #FirstOutCode := #FaultCodes[#i]; #latched := TRUE; END_IF;
   END_FOR;
   IF #AckEdge THEN #Acknowledged := TRUE; END_IF;
   IF #ResetEdge AND NOT #AnyFault THEN #latched := FALSE; #FirstOutCode := 0; #Acknowledged := FALSE; END_IF;
END_FUNCTION_BLOCK''',

        "FB_VisionInterface.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_VisionInterface"
VAR_INPUT Enable : Bool; TriggerEdge : Bool; InspectionId : UDInt; SessionEpoch : UDInt; ExpectedModelId : String[32]; ExpectedModelHash : String[64]; Ready : Bool; Busy : Bool; Result : "UDT_VisionResult"; Heartbeat : UDInt; Timeout : Time; HeartbeatTimeout : Time; ResetEdge : Bool; END_VAR
VAR_OUTPUT Trigger : Bool; Accepted : Bool; PublicationAck : Bool; QualityPass : Bool; HoldRequired : Bool; Fault : Bool; HeartbeatHealthy : Bool; ResultStuckHigh : Bool; DiagReason : "E_VisionDiag"; END_VAR
VAR
   tReady : TON; tResult : TON; tHeartbeat : TON; tResultClear : TON;
   pending : Bool; triggered : Bool; issuedOnce : Bool; heartbeatInitialized : Bool; resultMustClear : Bool; publicationWasAwaitingClear : Bool; heartbeatChanged : Bool; heartbeatRegressed : Bool;
   latchedId : UDInt; latchedSessionEpoch : UDInt; currentSessionEpoch : UDInt; lastIssuedId : UDInt; lastHeartbeat : UDInt;
END_VAR
BEGIN
   // Trigger and Accepted are one-scan pulses. Reset never synthesizes either edge.
   #Trigger := FALSE;
   #Accepted := FALSE;
   #PublicationAck := FALSE;

   // Transport ownership is independent of enable, transaction and quality.  The
   // exact publication ID is level-acknowledged until the edge deasserts VALID.
   #publicationWasAwaitingClear := #resultMustClear;
   IF #Result.ResultValid THEN #PublicationAck := TRUE; #resultMustClear := TRUE; END_IF;

   // Inspection IDs are strictly monotonic within one nonzero PLC session.
   // A session change resets the ID space only after pending/old publication clears.
   IF #SessionEpoch <> #currentSessionEpoch THEN
      IF #pending OR #Result.ResultValid THEN
         #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".SESSION_MISMATCH;
      ELSE
         #currentSessionEpoch := #SessionEpoch; #issuedOnce := FALSE; #lastIssuedId := UDINT#0; #resultMustClear := FALSE;
      END_IF;
   END_IF;

   // Heartbeat supervision is intentionally suppressed while disabled. On re-enable,
   // the current value becomes the baseline and must advance within HeartbeatTimeout.
   IF NOT #Enable THEN
      #heartbeatInitialized := FALSE; #heartbeatChanged := FALSE; #heartbeatRegressed := FALSE;
      #lastHeartbeat := #Heartbeat;
   ELSIF NOT #heartbeatInitialized THEN
      #heartbeatInitialized := TRUE; #heartbeatChanged := FALSE; #heartbeatRegressed := FALSE;
      #lastHeartbeat := #Heartbeat;
   ELSE
      #heartbeatChanged := #Heartbeat <> #lastHeartbeat;
      IF #heartbeatChanged THEN
         IF (#Heartbeat < #lastHeartbeat) AND NOT ((#lastHeartbeat > UDINT#4294967040) AND (#Heartbeat < UDINT#256)) THEN
            #heartbeatRegressed := TRUE;
         ELSIF NOT #heartbeatRegressed THEN
            #lastHeartbeat := #Heartbeat;
         END_IF;
      END_IF;
   END_IF;
   #tHeartbeat(IN := #Enable AND #heartbeatInitialized AND NOT #heartbeatChanged, PT := #HeartbeatTimeout);
   #HeartbeatHealthy := NOT #Enable OR (NOT #tHeartbeat.Q AND NOT #heartbeatRegressed);

   // A consumed or rejected publication must deassert before another request can arm.
   #tResultClear(IN := #resultMustClear AND #Result.ResultValid, PT := #Timeout);
   IF #resultMustClear AND NOT #Result.ResultValid THEN #resultMustClear := FALSE; END_IF;

   // Any publication while idle is orphaned, delayed or stuck and is never consumed.
   IF #Enable AND #Result.ResultValid AND NOT #pending AND NOT #publicationWasAwaitingClear THEN
      #ResultStuckHigh := TRUE; #Fault := TRUE; #HoldRequired := TRUE;
      IF #DiagReason = "E_VisionDiag".VISION_OK THEN #DiagReason := "E_VisionDiag".RESULT_STUCK_VALID; END_IF;
   END_IF;

   // READY=1/BUSY=1 means processing. BUSY without READY, or publication while
   // BUSY, is contradictory and fail-closed.
   IF #Enable AND ((#Busy AND NOT #Ready) OR (#Busy AND #Result.ResultValid)) AND NOT #Fault THEN
      #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".INTERFACE_CONTRADICTION;
   END_IF;

   IF #TriggerEdge AND #Enable AND NOT #Result.ResultValid AND NOT #pending AND NOT #Fault AND NOT #HoldRequired AND NOT #resultMustClear THEN
      IF #SessionEpoch = UDINT#0 THEN
         #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := "E_VisionDiag".SESSION_MISMATCH;
      ELSIF (#InspectionId = UDINT#0) OR (#issuedOnce AND ((#lastIssuedId = UDINT#4294967295) OR (#InspectionId <= #lastIssuedId))) THEN
         #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := "E_VisionDiag".NON_MONOTONIC_REQUEST;
      ELSE
         #pending := TRUE; #triggered := FALSE; #latchedId := #InspectionId; #latchedSessionEpoch := #SessionEpoch; #lastIssuedId := #InspectionId; #issuedOnce := TRUE; #QualityPass := FALSE;
      END_IF;
   END_IF;

   #tReady(IN := #pending AND NOT #triggered AND (NOT #Ready OR #Busy), PT := #Timeout);
   IF #pending AND NOT #triggered AND #Ready AND NOT #Busy AND NOT #Fault THEN #Trigger := TRUE; #triggered := TRUE; END_IF;
   #tResult(IN := #pending AND #triggered, PT := #Timeout);

   IF #pending AND #triggered AND #Result.ResultValid AND NOT #Fault THEN
      // Acknowledge transport ownership for every complete publication, including
      // rejected data. PublicationAck never means product acceptance.
      #PublicationAck := TRUE; #resultMustClear := TRUE;
      IF #Result.SessionEpoch <> #latchedSessionEpoch THEN
         #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".SESSION_MISMATCH;
      ELSIF #Result.ResultId <> #latchedId THEN
         #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".RESULT_ID_MISMATCH;
      ELSIF (#ExpectedModelId = '') OR (#ExpectedModelHash = '') OR (#Result.ModelId <> #ExpectedModelId) OR (#Result.ModelHash <> #ExpectedModelHash) THEN
         #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".MODEL_MISMATCH;
      ELSIF #Result.Fault OR #Result.Warning OR #Result.LowConfidence OR #Result.LeakOrSpill OR NOT (#Result.Bottle1Pass AND #Result.Bottle2Pass) OR (#Result.Fill1Status <> 2) OR (#Result.Fill2Status <> 2) THEN
         #Accepted := TRUE; #QualityPass := FALSE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".QUALITY_BLOCK;
      ELSE
         #Accepted := TRUE; #QualityPass := TRUE; #HoldRequired := FALSE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".VISION_OK;
      END_IF;
   END_IF;

   // First-out diagnostic is preserved once Fault is latched.
   IF NOT #Fault THEN
      IF #tReady.Q AND #pending AND NOT #triggered THEN #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".READY_TIMEOUT;
      ELSIF #tResult.Q AND #pending AND #triggered AND NOT #Result.ResultValid THEN #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #resultMustClear := TRUE; #DiagReason := "E_VisionDiag".RESULT_TIMEOUT;
      ELSIF NOT #HeartbeatHealthy THEN #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE; #DiagReason := "E_VisionDiag".HEARTBEAT_LOSS;
      ELSIF #tResultClear.Q THEN #ResultStuckHigh := TRUE; #Fault := TRUE; #HoldRequired := TRUE; IF #DiagReason = "E_VisionDiag".VISION_OK THEN #DiagReason := "E_VisionDiag".RESULT_STUCK_VALID; END_IF;
      END_IF;
   END_IF;

   IF NOT #Enable AND #pending THEN
      IF NOT #Fault THEN #DiagReason := "E_VisionDiag".INTERFACE_CONTRADICTION; END_IF;
      #Fault := TRUE; #HoldRequired := TRUE; #pending := FALSE; #triggered := FALSE;
   END_IF;
   IF #Fault THEN #Trigger := FALSE; #triggered := FALSE; END_IF;

   // Cause-cleared reset: publication low, interface coherent, heartbeat healthy,
   // request edge absent. The next request must carry an ID greater than lastIssuedId.
   IF #ResetEdge AND NOT #pending AND NOT #Busy AND NOT #Result.ResultValid AND NOT #TriggerEdge AND ((#Enable AND #Ready AND #HeartbeatHealthy) OR NOT #Enable) THEN
      #Fault := FALSE; #QualityPass := FALSE; #HoldRequired := FALSE; #ResultStuckHigh := FALSE; #resultMustClear := FALSE; #heartbeatRegressed := FALSE; #DiagReason := "E_VisionDiag".VISION_OK;
   END_IF;
END_FUNCTION_BLOCK''',

        "FB_FillChannel.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_FillChannel"
VAR_INPUT
   Enable : Bool; PumpRunning : Bool; StartEdge : Bool; Abort : Bool; ResetEdge : Bool;
   PulseTotal : UDInt; FlowRaw : Int; PulseChannelFault : Bool; AnalogChannelFault : Bool; ValveClosedFb : Bool;
   TargetMl : Real; PulsesPerLitre : Real; UnderToleranceMl : Real; OverToleranceMl : Real;
   FlowMaxLMin : Real; NoFlowMinLMin : Real; PlausibilityPct : Real; PulseWindowTimeS : Real;
   NoFlowTimeout : Time; FillTimeout : Time; ValveOpenTimeout : Time; ValveCloseTimeout : Time; PlausibilityTime : Time;
END_VAR
VAR_OUTPUT
   ValveOpenCmd : Bool; PumpRequest : Bool; Busy : Bool; Done : Bool; Fault : Bool; Underfill : Bool; Overfill : Bool;
   NoFlow : Bool; PulseMissing : Bool; AnalogNoFlow : Bool; ContinuedFlow : Bool; PulseAnalogDisagreement : Bool; AnalogBrokenWire : Bool;
   MeasurementWindowValid : Bool; CounterRolloverObserved : Bool; CounterDiscontinuity : Bool;
   DeliveredMl : Real; FlowLMin : Real; PulseFlowLMin : Real; DiagReason : "E_FillDiag";
END_VAR
VAR
   active : Bool; closing : Bool; initialized : Bool; configValid : Bool; comparisonArmed : Bool;
   pulsePresent : Bool; analogPresent : Bool; bothNoFlowCondition : Bool; pulseMissingCondition : Bool; analogNoFlowCondition : Bool; disagreementCondition : Bool;
   lastPulseTotal : UDInt; scanDelta : UDInt; accumulated : UDInt; targetPulses : UDInt; windowPulses : UDInt; windowCount : UInt;
   tWindow : TON; tPulseMissing : TON; tAnalogNoFlow : TON; tPlausibility : TON; tNoFlow : TON; tFill : TON; tValveOpen : TON; tValveClose : TON; tContinuedFlow : TON; tFlowStopped : TON;
END_VAR
BEGIN
   #MeasurementWindowValid := FALSE;
   IF NOT #initialized THEN
      #lastPulseTotal := #PulseTotal; #initialized := TRUE; #scanDelta := 0;
   ELSIF #PulseTotal >= #lastPulseTotal THEN
      #scanDelta := #PulseTotal - #lastPulseTotal;
   ELSIF (#lastPulseTotal > UDINT#4294967040) AND (#PulseTotal < UDINT#256) THEN
      // A high-to-low wrap is accepted as unsigned counter rollover.
      #scanDelta := (UDINT#4294967295 - #lastPulseTotal) + #PulseTotal + UDINT#1; #CounterRolloverObserved := TRUE;
   ELSE
      // Any other regression is a counter reset/discontinuity, not a rollover.
      #scanDelta := 0; #CounterDiscontinuity := TRUE;
   END_IF;
   #lastPulseTotal := #PulseTotal;
   #configValid := (#TargetMl > 0.0) AND (#PulsesPerLitre > 0.0) AND (#PulseWindowTimeS >= 0.1) AND (#FillTimeout > #NoFlowTimeout) AND (#OverToleranceMl >= 0.0) AND (#UnderToleranceMl >= 0.0);
   #AnalogBrokenWire := #AnalogChannelFault OR (#FlowRaw < 5000) OR (#FlowRaw > 29000);
   #FlowLMin := LIMIT(MN := 0.0, IN := INT_TO_REAL(#FlowRaw - 5530) * #FlowMaxLMin / 22118.0, MX := #FlowMaxLMin * 1.05);

   IF #StartEdge AND #Enable AND #ValveClosedFb AND NOT #Fault AND NOT #Busy THEN
      IF NOT #configValid THEN #Fault := TRUE; #DiagReason := "E_FillDiag".INVALID_CONFIG;
      ELSIF #AnalogBrokenWire THEN #Fault := TRUE; #DiagReason := "E_FillDiag".ANALOG_BROKEN_WIRE;
      ELSE
         #targetPulses := REAL_TO_UDINT(#TargetMl * #PulsesPerLitre / 1000.0); #accumulated := 0; #windowPulses := 0; #windowCount := 0; #scanDelta := 0; #lastPulseTotal := #PulseTotal;
         #active := TRUE; #closing := FALSE; #comparisonArmed := FALSE; #Done := FALSE; #Underfill := FALSE; #Overfill := FALSE; #NoFlow := FALSE;
         #PulseMissing := FALSE; #AnalogNoFlow := FALSE; #ContinuedFlow := FALSE; #PulseAnalogDisagreement := FALSE; #CounterRolloverObserved := FALSE; #CounterDiscontinuity := FALSE;
         #bothNoFlowCondition := FALSE; #pulseMissingCondition := FALSE; #analogNoFlowCondition := FALSE; #disagreementCondition := FALSE; #DiagReason := "E_FillDiag".FILL_OK;
      END_IF;
   END_IF;

   IF #active THEN #accumulated := #accumulated + #scanDelta; #windowPulses := #windowPulses + #scanDelta; END_IF;
   #DeliveredMl := UDINT_TO_REAL(#accumulated) * 1000.0 / MAX(IN1 := #PulsesPerLitre, IN2 := 1.0);
   #PumpRequest := #active AND #Enable AND NOT #Abort AND NOT #Fault AND (#accumulated < #targetPulses) AND NOT #Overfill;
   #ValveOpenCmd := #PumpRequest AND #PumpRunning;
   #Busy := #active OR #closing;

   // A complete measurement window is explicit. The first complete window is a
   // startup/acceleration settling window; comparisons arm from window two.
   #tWindow(IN := #ValveOpenCmd AND NOT #tWindow.Q, PT := REAL_TO_TIME(#PulseWindowTimeS * 1000.0));
   IF #tWindow.Q THEN
      #MeasurementWindowValid := TRUE;
      #PulseFlowLMin := UDINT_TO_REAL(#windowPulses) * 60.0 / (#PulsesPerLitre * #PulseWindowTimeS);
      #windowPulses := 0;
      IF #windowCount < UINT#65535 THEN #windowCount := #windowCount + UINT#1; END_IF;
      #comparisonArmed := #windowCount >= UINT#2;
      IF #comparisonArmed THEN
         #pulsePresent := #PulseFlowLMin >= #NoFlowMinLMin;
         #analogPresent := #FlowLMin >= #NoFlowMinLMin;
         #bothNoFlowCondition := NOT #pulsePresent AND NOT #analogPresent;
         #pulseMissingCondition := NOT #pulsePresent AND #analogPresent;
         #analogNoFlowCondition := #pulsePresent AND NOT #analogPresent;
         #disagreementCondition := #pulsePresent AND #analogPresent AND ((ABS(#PulseFlowLMin - #FlowLMin) * 100.0) > (#PlausibilityPct * MAX(IN1 := #FlowLMin, IN2 := 0.1)));
      END_IF;
   END_IF;

   #tNoFlow(IN := #ValveOpenCmd AND #comparisonArmed AND #bothNoFlowCondition, PT := #NoFlowTimeout);
   #tPulseMissing(IN := #ValveOpenCmd AND #comparisonArmed AND #pulseMissingCondition, PT := #PlausibilityTime);
   #tAnalogNoFlow(IN := #ValveOpenCmd AND #comparisonArmed AND #analogNoFlowCondition, PT := #PlausibilityTime);
   #tPlausibility(IN := #ValveOpenCmd AND #comparisonArmed AND #disagreementCondition, PT := #PlausibilityTime);
   // Target attainment on the discrete deadline scan wins over fill timeout.
   #tFill(IN := #active AND (#accumulated < #targetPulses), PT := #FillTimeout); #tValveOpen(IN := #ValveOpenCmd AND #ValveClosedFb, PT := #ValveOpenTimeout);
   #tValveClose(IN := #closing AND NOT #ValveClosedFb, PT := #ValveCloseTimeout);
   #tContinuedFlow(IN := #closing AND ((#scanDelta > 0) OR (#FlowLMin > #NoFlowMinLMin)), PT := #NoFlowTimeout);
   #tFlowStopped(IN := #closing AND #ValveClosedFb AND (#scanDelta = 0) AND (#FlowLMin <= #NoFlowMinLMin), PT := #NoFlowTimeout);

   // First-out priority is channel health, missing pulse, missing analog, both-no-flow,
   // cross-channel disagreement, feedback mismatch, then general timeout.
   IF NOT #Fault THEN
      IF #PulseChannelFault OR #CounterDiscontinuity THEN #Fault := TRUE; #DiagReason := "E_FillDiag".PULSE_COUNTER_DISCONTINUITY;
      ELSIF #AnalogBrokenWire THEN #Fault := TRUE; #DiagReason := "E_FillDiag".ANALOG_BROKEN_WIRE;
      ELSIF #tPulseMissing.Q THEN #PulseMissing := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".PULSE_MISSING;
      ELSIF #tAnalogNoFlow.Q THEN #AnalogNoFlow := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".ANALOG_NO_FLOW;
      ELSIF #tNoFlow.Q THEN #NoFlow := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".NO_FLOW;
      ELSIF #tPlausibility.Q THEN #PulseAnalogDisagreement := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".PULSE_ANALOG_DISAGREE;
      ELSIF #tValveOpen.Q THEN #Fault := TRUE; #DiagReason := "E_FillDiag".VALVE_OPEN_MISMATCH;
      ELSIF #tFill.Q THEN #Fault := TRUE; #DiagReason := "E_FillDiag".FILL_TIMEOUT;
      END_IF;
   END_IF;
   IF NOT #Fault AND #Busy AND (#DeliveredMl > (#TargetMl + #OverToleranceMl)) THEN #Overfill := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".OVERFILL; END_IF;
   IF #active AND ((#accumulated >= #targetPulses) OR #Abort OR #Fault OR NOT #Enable) THEN #active := FALSE; #closing := TRUE; END_IF;
   IF NOT #Fault AND #tContinuedFlow.Q THEN #ContinuedFlow := TRUE; #Fault := TRUE; #DiagReason := "E_FillDiag".CONTINUED_FLOW; END_IF;
   IF NOT #Fault AND #tValveClose.Q THEN #Fault := TRUE; #DiagReason := "E_FillDiag".VALVE_CLOSE_MISMATCH; END_IF;
   IF NOT #Fault AND #Abort AND #Busy THEN #Fault := TRUE; #DiagReason := "E_FillDiag".ABORTED; END_IF;
   IF #tFlowStopped.Q AND NOT #tContinuedFlow.Q THEN
      #closing := FALSE; #Underfill := #DeliveredMl < (#TargetMl - #UnderToleranceMl); #Overfill := #DeliveredMl > (#TargetMl + #OverToleranceMl);
      #Done := NOT (#Underfill OR #Overfill OR #Fault); IF #Underfill AND NOT #Fault THEN #Fault := TRUE; #DiagReason := "E_FillDiag".UNDERFILL; END_IF;
   END_IF;
   IF #ResetEdge AND NOT #StartEdge AND NOT #active AND NOT #closing AND #ValveClosedFb AND NOT #PulseChannelFault AND NOT #AnalogBrokenWire AND (#FlowLMin <= #NoFlowMinLMin) AND (#scanDelta = 0) AND #configValid THEN
      #Fault := FALSE; #Done := FALSE; #Underfill := FALSE; #Overfill := FALSE; #NoFlow := FALSE; #PulseMissing := FALSE; #AnalogNoFlow := FALSE; #ContinuedFlow := FALSE;
      #PulseAnalogDisagreement := FALSE; #comparisonArmed := FALSE; #bothNoFlowCondition := FALSE; #pulseMissingCondition := FALSE; #analogNoFlowCondition := FALSE; #disagreementCondition := FALSE;
      #closing := FALSE; #CounterDiscontinuity := FALSE; #accumulated := 0; #windowPulses := 0; #windowCount := 0; #DeliveredMl := 0.0; #DiagReason := "E_FillDiag".FILL_OK;
   END_IF;
END_FUNCTION_BLOCK''',

        "FB_CapperInterface.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_CapperInterface"
VAR_INPUT Enable : Bool; RequestEdge : Bool; Ready : Bool; Busy : Bool; Complete : Bool; FaultIn : Bool; ResetEdge : Bool; AcceptTimeout : Time; CompleteTimeout : Time; END_VAR
VAR_OUTPUT Request : Bool; Accepted : Bool; CompletePulse : Bool; HoldRequired : Bool; Fault : Bool; DiagReason : UInt; END_VAR
VAR tReady : TON; tAccept : TON; tComplete : TON; pending : Bool; seenBusy : Bool; END_VAR
BEGIN
   #CompletePulse := FALSE;
   IF #RequestEdge AND #Enable AND NOT #pending AND NOT #Fault THEN
      IF #Busy OR #Complete THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 5;
      ELSE #pending := TRUE; #Request := FALSE; #seenBusy := FALSE; #Accepted := FALSE; END_IF;
   END_IF;
   #tReady(IN := #pending AND NOT #Ready AND NOT #seenBusy, PT := #AcceptTimeout);
   IF #pending AND #Ready AND NOT #Busy AND NOT #seenBusy THEN #Request := TRUE; END_IF;
   // BUSY is correlated only after this transaction asserted REQUEST. A
   // pre-existing BUSY can belong to another bottle and must never be accepted.
   IF #pending AND #Request AND #Busy THEN #seenBusy := TRUE; #Accepted := TRUE; END_IF;
   #tAccept(IN := #pending AND #Ready AND #Request AND NOT #seenBusy, PT := #AcceptTimeout);
   #tComplete(IN := #pending AND #seenBusy AND NOT #Complete, PT := #CompleteTimeout);
   IF #pending AND #seenBusy AND #Complete THEN #CompletePulse := TRUE; #Request := FALSE; #pending := FALSE; #Accepted := FALSE; END_IF;
   IF #FaultIn THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 1;
   ELSIF #tReady.Q THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 2;
   ELSIF #tAccept.Q THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 3;
   ELSIF #tComplete.Q THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 4;
   ELSIF (#Complete AND NOT #seenBusy) OR (#pending AND #Busy AND NOT #Request) THEN #Fault := TRUE; #HoldRequired := TRUE; #DiagReason := 5; END_IF;
   IF #Fault THEN #Request := FALSE; #pending := FALSE; #Accepted := FALSE; END_IF;
   IF #ResetEdge AND #Ready AND NOT #FaultIn AND NOT #Busy AND NOT #Complete AND NOT #RequestEdge AND NOT #pending THEN #Fault := FALSE; #HoldRequired := FALSE; #Accepted := FALSE; #DiagReason := 0; END_IF;
END_FUNCTION_BLOCK''',

        "FB_MachineCoordinator.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_MachineCoordinator"
VAR_INPUT InitDone : Bool; PermissivesOk : Bool; StartEdge : Bool; StopEdge : Bool; ResetEdge : Bool; AutoRequest : Bool; ManualRequest : Bool; DispositionRemoved : Bool; PairPresent : Bool; PairAbsent : Bool; ConveyorStopped : Bool; GateClosed : Bool; GateOpen : Bool; ClampEngaged : Bool; ClampReleased : Bool; Fill1Done : Bool; Fill2Done : Bool; DripDone : Bool; VisionAccepted : Bool; VisionPass : Bool; CapperReady : Bool; CapperComplete : Bool; BlockingFault : Bool; END_VAR
VAR_OUTPUT State : "E_MachineState"; AutoStep : "E_AutoStep"; IndexRequest : Bool; GateCloseRequest : Bool; ClampRequest : Bool; FillStartPulse : Bool; VisionRequestPulse : Bool; CapperRequestPulse : Bool; QualityHold : Bool; DispositionRequired : Bool; END_VAR
BEGIN
   #FillStartPulse := FALSE; #VisionRequestPulse := FALSE; #CapperRequestPulse := FALSE;
   CASE #State OF
      "E_MachineState".UNINITIALIZED: IF #InitDone THEN #State := "E_MachineState".INITIALIZING; END_IF;
      "E_MachineState".INITIALIZING: IF #BlockingFault THEN #DispositionRequired := NOT #PairAbsent; #State := "E_MachineState".FAULTED; ELSE #State := "E_MachineState".STOPPED; END_IF;
      "E_MachineState".STOPPED: #IndexRequest := FALSE; #GateCloseRequest := FALSE; #ClampRequest := FALSE; #QualityHold := #DispositionRequired; IF #DispositionRequired THEN #State := "E_MachineState".HOLDING; ELSIF #ResetEdge AND #PermissivesOk THEN #State := "E_MachineState".READY; END_IF;
      "E_MachineState".READY: IF #BlockingFault THEN #DispositionRequired := NOT #PairAbsent; #State := "E_MachineState".FAULTED; ELSIF #ManualRequest THEN #State := "E_MachineState".MANUAL_SETUP; ELSIF #StartEdge AND #PermissivesOk THEN #DispositionRequired := FALSE; #AutoStep := "E_AutoStep".WAIT_PAIR; #State := "E_MachineState".AUTOMATIC; END_IF;
      "E_MachineState".AUTOMATIC:
         IF #BlockingFault THEN #DispositionRequired := (NOT #PairAbsent) OR (#AutoStep <> "E_AutoStep".WAIT_PAIR); #State := "E_MachineState".FAULTED;
         ELSIF #StopEdge THEN #DispositionRequired := (NOT #PairAbsent) OR (#AutoStep <> "E_AutoStep".WAIT_PAIR); #State := "E_MachineState".CONTROLLED_STOPPING;
         ELSE
            CASE #AutoStep OF
               "E_AutoStep".WAIT_PAIR: #IndexRequest := TRUE; IF #PairPresent THEN #IndexRequest := FALSE; #AutoStep := "E_AutoStep".SECURE_PAIR; END_IF;
               "E_AutoStep".SECURE_PAIR: #GateCloseRequest := TRUE; #ClampRequest := TRUE; IF #ConveyorStopped AND #GateClosed AND #ClampEngaged THEN #FillStartPulse := TRUE; #AutoStep := "E_AutoStep".FILL_PAIR; END_IF;
               "E_AutoStep".FILL_PAIR: IF #Fill1Done AND #Fill2Done THEN #AutoStep := "E_AutoStep".DRIP_SETTLE; END_IF;
               "E_AutoStep".DRIP_SETTLE: IF #DripDone THEN #VisionRequestPulse := TRUE; #AutoStep := "E_AutoStep".INSPECT; END_IF;
               "E_AutoStep".INSPECT: IF #VisionAccepted THEN IF #VisionPass THEN #CapperRequestPulse := TRUE; #AutoStep := "E_AutoStep".TRANSFER; ELSE #DispositionRequired := TRUE; #QualityHold := TRUE; #State := "E_MachineState".HOLDING; END_IF; END_IF;
               "E_AutoStep".TRANSFER: IF #CapperComplete THEN #GateCloseRequest := FALSE; #ClampRequest := FALSE; #AutoStep := "E_AutoStep".RELEASE_PAIR; END_IF;
               "E_AutoStep".RELEASE_PAIR: IF #GateOpen AND #ClampReleased AND #PairAbsent THEN #DispositionRequired := FALSE; #AutoStep := "E_AutoStep".WAIT_PAIR; #State := "E_MachineState".READY; END_IF;
            END_CASE;
         END_IF;
      "E_MachineState".MANUAL_SETUP: IF #BlockingFault THEN #DispositionRequired := NOT #PairAbsent; #State := "E_MachineState".FAULTED; ELSIF #StopEdge THEN #DispositionRequired := NOT #PairAbsent; #State := "E_MachineState".CONTROLLED_STOPPING; ELSIF #AutoRequest THEN #State := "E_MachineState".READY; END_IF;
      "E_MachineState".HOLDING: #QualityHold := TRUE; IF #DispositionRemoved AND #PairAbsent AND NOT #BlockingFault THEN #DispositionRequired := FALSE; #State := "E_MachineState".RECOVERY_RESET; END_IF;
      "E_MachineState".CONTROLLED_STOPPING: #IndexRequest := FALSE; IF #ConveyorStopped THEN IF #DispositionRequired THEN #State := "E_MachineState".HOLDING; ELSE #State := "E_MachineState".STOPPED; END_IF; END_IF;
      "E_MachineState".FAULTED: #IndexRequest := FALSE; #QualityHold := TRUE; IF #ResetEdge AND NOT #BlockingFault THEN IF #DispositionRequired THEN #State := "E_MachineState".HOLDING; ELSE #State := "E_MachineState".RECOVERY_RESET; END_IF; END_IF;
      "E_MachineState".RECOVERY_RESET: #IndexRequest := FALSE; #GateCloseRequest := FALSE; #ClampRequest := FALSE; #QualityHold := FALSE; #State := "E_MachineState".STOPPED;
   END_CASE;
   IF #BlockingFault THEN #IndexRequest := FALSE; #FillStartPulse := FALSE; #VisionRequestPulse := FALSE; #CapperRequestPulse := FALSE; END_IF;
END_FUNCTION_BLOCK''',

        "FB_CellMain.scl": f'''// {NOTICE}
FUNCTION_BLOCK "FB_CellMain"
VAR
   HmiCommands : "FB_HMICommandManager";
   ConveyorVfd : "FB_VFD";
   PumpVfd : "FB_VFD";
   Gate : "FB_Actuator2Pos";
   Clamp : "FB_Actuator2Pos";
   FillCh1 : "FB_FillChannel";
   FillCh2 : "FB_FillChannel";
   Vision : "FB_VisionInterface";
   Capper : "FB_CapperInterface";
   Recipe : "FB_RecipeManager";
   Alarm : "FB_AlarmManager";
   Coordinator : "FB_MachineCoordinator";
   DripTimer : TON;
   PlcHeartbeatTimer : TON;
   blockingFault : Bool;
   outputInterlock : Bool;
   preBlockingFault : Bool;
   immediateStop : Bool;
   processPermissive : Bool;
   modelConfigured : Bool;
   manualConveyorInterlocked : Bool;
   manualSecureInterlocked : Bool;
   manualPumpInterlocked : Bool;
   manualValve1Interlocked : Bool;
   manualValve2Interlocked : Bool;
   activeFaults : Array[0..31] of Bool;
   faultCodes : Array[0..31] of UInt;
   i : Int;
END_VAR
BEGIN
   // Input normalization from process image.
   "DB_IO".Inputs.SafetyOk := %I0.0;
   "DB_IO".Inputs.GuardClosed := %I0.1;
   "DB_IO".Inputs.AirPressureOk := %I0.2;
   "DB_IO".Inputs.ProductSupplyOk := %I0.3;
   "DB_IO".Inputs.Bottle1Present := %I1.2;
   "DB_IO".Inputs.Bottle2Present := %I1.3;
   "DB_IO".Inputs.GateOpen := %I1.4;
   "DB_IO".Inputs.GateClosed := %I1.5;
   "DB_IO".Inputs.ClampReleased := %I1.6;
   "DB_IO".Inputs.ClampEngaged := %I1.7;
   "DB_IO".Inputs.Valve1Closed := %I2.0;
   "DB_IO".Inputs.Valve2Closed := %I2.1;
   "DB_IO".Inputs.CapperReady := %I2.2;
   "DB_IO".Inputs.CapperBusy := %I2.3;
   "DB_IO".Inputs.CapperComplete := %I2.4;
   "DB_IO".Inputs.CapperFault := %I2.5;
   "DB_IO".Inputs.LocalReset := %I2.6;
   "DB_IO".Inputs.LocalStop := %I2.7;
   "DB_IO".Inputs.Flow1Raw := %IW64;
   "DB_IO".Inputs.Flow2Raw := %IW66;
   // Native-project adapter contract. Bind these fields to PN diagnostics and TM Count technology-object outputs in TIA V20.
   "DB_IO".Inputs.ConveyorPnHealthy := "DB_NativeBindings".Inputs.ConveyorPnIoValid;
   "DB_IO".Inputs.PumpPnHealthy := "DB_NativeBindings".Inputs.PumpPnIoValid;
   "DB_IO".Inputs.PulseTotal1 := "DB_NativeBindings".Inputs.Flow1PulseTotal;
   "DB_IO".Inputs.PulseTotal2 := "DB_NativeBindings".Inputs.Flow2PulseTotal;
   "DB_IO".Inputs.Flow1ChannelFault := "DB_NativeBindings".Inputs.Flow1ChannelFault;
   "DB_IO".Inputs.Flow2ChannelFault := "DB_NativeBindings".Inputs.Flow2ChannelFault;
   "DB_IO".Inputs.Flow1PulseChannelFault := "DB_NativeBindings".Inputs.Flow1PulseChannelFault;
   "DB_IO".Inputs.Flow2PulseChannelFault := "DB_NativeBindings".Inputs.Flow2PulseChannelFault;
   "DB_Drives".Conveyor.StatusWord1 := %IW256;
   "DB_Drives".Conveyor.ActualSpeedPzd := %IW258;
   "DB_Drives".Pump.StatusWord1 := %IW260;
   "DB_Drives".Pump.ActualSpeedPzd := %IW262;

   #modelConfigured := "DB_VisionComms".ModelConfigurationApproved AND ("DB_VisionComms".ExpectedModelId <> '') AND (LEN("DB_VisionComms".ExpectedModelHash) = 64);
   #immediateStop := NOT "DB_IO".Inputs.SafetyOk OR NOT "DB_IO".Inputs.GuardClosed OR NOT "DB_IO".Inputs.AirPressureOk OR NOT "DB_IO".Inputs.ProductSupplyOk;
   #processPermissive := NOT #immediateStop AND NOT "DB_IO".PowerRecoveryRequired;
   #preBlockingFault := #immediateStop OR #ConveyorVfd.Fault OR #PumpVfd.Fault OR #Gate.Fault OR #Clamp.Fault OR #FillCh1.Fault OR #FillCh2.Fault OR #Vision.Fault OR NOT #modelConfigured OR NOT "DB_VisionComms".Ready OR #Capper.Fault OR NOT #HmiCommands.CommunicationsHealthy;
   #HmiCommands(StartRequest := "DB_HMI".Start.Request, StartSeq := "DB_HMI".Start.RequestSeq, StopRequest := "DB_HMI".ControlledStop.Request, StopSeq := "DB_HMI".ControlledStop.RequestSeq, ResetRequest := "DB_HMI".Reset.Request, ResetSeq := "DB_HMI".Reset.RequestSeq, AckRequest := "DB_HMI".AlarmAck.Request, AckSeq := "DB_HMI".AlarmAck.RequestSeq, AutoRequest := "DB_HMI".AutoMode.Request, AutoSeq := "DB_HMI".AutoMode.RequestSeq, ManualRequest := "DB_HMI".ManualMode.Request, ManualSeq := "DB_HMI".ManualMode.RequestSeq, DispositionRequest := "DB_HMI".DispositionRemoved.Request, DispositionSeq := "DB_HMI".DispositionRemoved.RequestSeq, ManualConveyorRequest := "DB_HMI".ManualConveyorJog.Request, ManualPumpRequest := "DB_HMI".ManualPumpJog.Request, ManualValve1Request := "DB_HMI".ManualValve1.Request, ManualValve2Request := "DB_HMI".ManualValve2.Request, ManualSecureRequest := "DB_HMI".ManualSecure.Request, ManualHoldAllowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP) AND #processPermissive, LocalStop := "DB_IO".Inputs.LocalStop, LocalReset := "DB_IO".Inputs.LocalReset, CommandHeartbeat := "DB_HMI".CommandHeartbeat, StartAllowed := (#Coordinator.State = "E_MachineState".READY) AND #processPermissive, ResetAllowed := NOT #immediateStop, AutoAllowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP), ManualAllowed := (#Coordinator.State = "E_MachineState".READY), DispositionAllowed := (#Coordinator.State = "E_MachineState".HOLDING));
   "DB_HMI".Start.AcceptedSeq := #HmiCommands.StartAcceptedSeq; "DB_HMI".Start.RejectedSeq := #HmiCommands.StartRejectedSeq;
   "DB_HMI".ControlledStop.AcceptedSeq := #HmiCommands.StopAcceptedSeq;
   "DB_HMI".Reset.AcceptedSeq := #HmiCommands.ResetAcceptedSeq; "DB_HMI".Reset.RejectedSeq := #HmiCommands.ResetRejectedSeq;
   "DB_HMI".AlarmAck.AcceptedSeq := #HmiCommands.AckAcceptedSeq;
   "DB_HMI".AutoMode.AcceptedSeq := #HmiCommands.AutoAcceptedSeq; "DB_HMI".AutoMode.RejectedSeq := #HmiCommands.AutoRejectedSeq;
   "DB_HMI".ManualMode.AcceptedSeq := #HmiCommands.ManualAcceptedSeq; "DB_HMI".ManualMode.RejectedSeq := #HmiCommands.ManualRejectedSeq;
   "DB_HMI".DispositionRemoved.AcceptedSeq := #HmiCommands.DispositionAcceptedSeq; "DB_HMI".DispositionRemoved.RejectedSeq := #HmiCommands.DispositionRejectedSeq;
   "DB_HMI".CommunicationsHealthy := #HmiCommands.CommunicationsHealthy;
   #manualConveyorInterlocked := #HmiCommands.ManualConveyorCmd AND NOT #HmiCommands.ManualSecureCmd AND NOT #HmiCommands.ManualPumpCmd AND NOT #HmiCommands.ManualValve1Cmd AND NOT #HmiCommands.ManualValve2Cmd AND "DB_IO".Inputs.GateOpen AND "DB_IO".Inputs.ClampReleased;
   #manualSecureInterlocked := #HmiCommands.ManualSecureCmd AND NOT #HmiCommands.ManualConveyorCmd AND #ConveyorVfd.Stopped;
   #manualPumpInterlocked := #HmiCommands.ManualPumpCmd AND #manualSecureInterlocked AND #ConveyorVfd.Stopped AND "DB_IO".Inputs.GateClosed AND "DB_IO".Inputs.ClampEngaged AND (#HmiCommands.ManualValve1Cmd OR #HmiCommands.ManualValve2Cmd);
   #manualValve1Interlocked := #HmiCommands.ManualValve1Cmd AND #manualPumpInterlocked AND #PumpVfd.Running;
   #manualValve2Interlocked := #HmiCommands.ManualValve2Cmd AND #manualPumpInterlocked AND #PumpVfd.Running;
   "DB_HMI".Start.Allowed := (#Coordinator.State = "E_MachineState".READY) AND #processPermissive; "DB_HMI".Start.Busy := FALSE; "DB_HMI".Start.DisabledReason := 0; IF NOT "DB_HMI".Start.Allowed THEN "DB_HMI".Start.DisabledReason := 1; END_IF;
   "DB_HMI".ControlledStop.Allowed := TRUE; "DB_HMI".ControlledStop.Busy := FALSE; "DB_HMI".ControlledStop.DisabledReason := 0;
   "DB_HMI".Reset.Allowed := NOT #immediateStop; "DB_HMI".Reset.Busy := FALSE; "DB_HMI".Reset.DisabledReason := 0; IF NOT "DB_HMI".Reset.Allowed THEN "DB_HMI".Reset.DisabledReason := 2; END_IF;
   "DB_HMI".AlarmAck.Allowed := TRUE; "DB_HMI".AlarmAck.Busy := FALSE; "DB_HMI".AlarmAck.DisabledReason := 0;
   "DB_HMI".AutoMode.Allowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP); "DB_HMI".AutoMode.Busy := FALSE; "DB_HMI".AutoMode.DisabledReason := 0; IF NOT "DB_HMI".AutoMode.Allowed THEN "DB_HMI".AutoMode.DisabledReason := 4; END_IF;
   "DB_HMI".ManualMode.Allowed := (#Coordinator.State = "E_MachineState".READY); "DB_HMI".ManualMode.Busy := FALSE; "DB_HMI".ManualMode.DisabledReason := 0; IF NOT "DB_HMI".ManualMode.Allowed THEN "DB_HMI".ManualMode.DisabledReason := 4; END_IF;
   "DB_HMI".DispositionRemoved.Allowed := (#Coordinator.State = "E_MachineState".HOLDING); "DB_HMI".DispositionRemoved.Busy := FALSE; "DB_HMI".DispositionRemoved.DisabledReason := 0;
   "DB_HMI".ManualConveyorJog.Allowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP) AND #processPermissive AND NOT #HmiCommands.ManualSecureCmd AND NOT #HmiCommands.ManualPumpCmd AND NOT #HmiCommands.ManualValve1Cmd AND NOT #HmiCommands.ManualValve2Cmd AND "DB_IO".Inputs.GateOpen AND "DB_IO".Inputs.ClampReleased; "DB_HMI".ManualConveyorJog.Busy := #manualConveyorInterlocked; "DB_HMI".ManualConveyorJog.DisabledReason := 0; IF NOT "DB_HMI".ManualConveyorJog.Allowed THEN "DB_HMI".ManualConveyorJog.DisabledReason := 5; END_IF;
   "DB_HMI".ManualPumpJog.Allowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP) AND #processPermissive AND #manualSecureInterlocked AND #ConveyorVfd.Stopped AND "DB_IO".Inputs.GateClosed AND "DB_IO".Inputs.ClampEngaged; "DB_HMI".ManualPumpJog.Busy := #manualPumpInterlocked; "DB_HMI".ManualPumpJog.DisabledReason := 0; IF NOT "DB_HMI".ManualPumpJog.Allowed THEN "DB_HMI".ManualPumpJog.DisabledReason := 6; END_IF;
   "DB_HMI".ManualValve1.Allowed := "DB_HMI".ManualPumpJog.Allowed; "DB_HMI".ManualValve1.Busy := #manualValve1Interlocked; "DB_HMI".ManualValve1.DisabledReason := "DB_HMI".ManualPumpJog.DisabledReason;
   "DB_HMI".ManualValve2.Allowed := "DB_HMI".ManualPumpJog.Allowed; "DB_HMI".ManualValve2.Busy := #manualValve2Interlocked; "DB_HMI".ManualValve2.DisabledReason := "DB_HMI".ManualPumpJog.DisabledReason;
   "DB_HMI".ManualSecure.Allowed := (#Coordinator.State = "E_MachineState".MANUAL_SETUP) AND #processPermissive AND #ConveyorVfd.Stopped AND NOT #HmiCommands.ManualConveyorCmd; "DB_HMI".ManualSecure.Busy := #manualSecureInterlocked; "DB_HMI".ManualSecure.DisabledReason := 0; IF NOT "DB_HMI".ManualSecure.Allowed THEN "DB_HMI".ManualSecure.DisabledReason := 7; END_IF;

   #Recipe(Candidate := "DB_Recipe".Candidate, ApplyRequest := "DB_HMI".RecipeApply.Request AND #HmiCommands.CommunicationsHealthy, RequestSeq := "DB_HMI".RecipeApply.RequestSeq, MachineStopped := (#Coordinator.State = "E_MachineState".STOPPED));
   "DB_Recipe".Active := #Recipe.Active;
   "DB_HMI".RecipeApply.AcceptedSeq := #Recipe.AcceptedSeq; "DB_HMI".RecipeApply.RejectedSeq := #Recipe.RejectedSeq;
   "DB_HMI".RecipeApply.Allowed := (#Coordinator.State = "E_MachineState".STOPPED) AND #Recipe.Valid; "DB_HMI".RecipeApply.Busy := FALSE; "DB_HMI".RecipeApply.DisabledReason := 0; IF NOT #Recipe.Valid THEN "DB_HMI".RecipeApply.DisabledReason := 3; END_IF;

   "DB_Drives".Conveyor.CommsHealthy := "DB_IO".Inputs.ConveyorPnHealthy; "DB_Drives".Pump.CommsHealthy := "DB_IO".Inputs.PumpPnHealthy;
   #ConveyorVfd(Enable := "DB_IO".Inputs.SafetyOk AND "DB_IO".Inputs.GuardClosed, RunRequest := (#Coordinator.IndexRequest OR #manualConveyorInterlocked) AND NOT #immediateStop, ResetEdge := #HmiCommands.ResetPulse, CommsHealthy := "DB_Drives".Conveyor.CommsHealthy, StatusWord1 := "DB_Drives".Conveyor.StatusWord1, ActualSpeedPzd := "DB_Drives".Conveyor.ActualSpeedPzd, SpeedReferencePct := 35.0, StartTimeout := T#3s, StopTimeout := T#3s);
   #PumpVfd(Enable := #processPermissive, RunRequest := ((#FillCh1.PumpRequest OR #FillCh2.PumpRequest) OR #manualPumpInterlocked) AND #processPermissive, ResetEdge := #HmiCommands.ResetPulse, CommsHealthy := "DB_Drives".Pump.CommsHealthy, StatusWord1 := "DB_Drives".Pump.StatusWord1, ActualSpeedPzd := "DB_Drives".Pump.ActualSpeedPzd, SpeedReferencePct := 60.0, StartTimeout := T#3s, StopTimeout := T#3s);
   "DB_Drives".Conveyor.Ready := #ConveyorVfd.Ready; "DB_Drives".Conveyor.Running := #ConveyorVfd.Running; "DB_Drives".Conveyor.Fault := #ConveyorVfd.Fault; "DB_Drives".Conveyor.ActualSpeedPct := #ConveyorVfd.ActualSpeedPct;
   "DB_Drives".Pump.Ready := #PumpVfd.Ready; "DB_Drives".Pump.Running := #PumpVfd.Running; "DB_Drives".Pump.Fault := #PumpVfd.Fault; "DB_Drives".Pump.ActualSpeedPct := #PumpVfd.ActualSpeedPct;
   #Gate(Enable := NOT #immediateStop, CmdToA := NOT (#Coordinator.GateCloseRequest OR #manualSecureInterlocked), CmdToB := #Coordinator.GateCloseRequest OR #manualSecureInterlocked, AtA := "DB_IO".Inputs.GateOpen, AtB := "DB_IO".Inputs.GateClosed, ResetEdge := #HmiCommands.ResetPulse, TravelTime := T#2s);
   #Clamp(Enable := NOT #immediateStop, CmdToA := NOT (#Coordinator.ClampRequest OR #manualSecureInterlocked), CmdToB := #Coordinator.ClampRequest OR #manualSecureInterlocked, AtA := "DB_IO".Inputs.ClampReleased, AtB := "DB_IO".Inputs.ClampEngaged, ResetEdge := #HmiCommands.ResetPulse, TravelTime := T#2s);
   #FillCh1(Enable := #processPermissive, PumpRunning := #PumpVfd.Running, StartEdge := #Coordinator.FillStartPulse, Abort := #preBlockingFault OR #ConveyorVfd.Fault OR #PumpVfd.Fault OR #Gate.Fault OR #Clamp.Fault OR #HmiCommands.StopPulse, ResetEdge := #HmiCommands.ResetPulse, PulseTotal := "DB_IO".Inputs.PulseTotal1, FlowRaw := "DB_IO".Inputs.Flow1Raw, PulseChannelFault := "DB_IO".Inputs.Flow1PulseChannelFault, AnalogChannelFault := "DB_IO".Inputs.Flow1ChannelFault, ValveClosedFb := "DB_IO".Inputs.Valve1Closed, TargetMl := "DB_Recipe".Active.TargetMlCh1, PulsesPerLitre := "DB_Recipe".Active.PulsesPerLitreCh1, UnderToleranceMl := "DB_Recipe".Active.UnderToleranceMl, OverToleranceMl := "DB_Recipe".Active.OverToleranceMl, FlowMaxLMin := 20.0, NoFlowMinLMin := 0.2, PlausibilityPct := 25.0, PulseWindowTimeS := "DB_Recipe".Active.PulseWindowTimeS, NoFlowTimeout := "DB_Recipe".Active.NoFlowTimeout, FillTimeout := "DB_Recipe".Active.FillTimeout, ValveOpenTimeout := "DB_Recipe".Active.ValveOpenTimeout, ValveCloseTimeout := "DB_Recipe".Active.ValveCloseTimeout, PlausibilityTime := "DB_Recipe".Active.PlausibilityTime);
   #FillCh2(Enable := #processPermissive, PumpRunning := #PumpVfd.Running, StartEdge := #Coordinator.FillStartPulse, Abort := #preBlockingFault OR #ConveyorVfd.Fault OR #PumpVfd.Fault OR #Gate.Fault OR #Clamp.Fault OR #HmiCommands.StopPulse, ResetEdge := #HmiCommands.ResetPulse, PulseTotal := "DB_IO".Inputs.PulseTotal2, FlowRaw := "DB_IO".Inputs.Flow2Raw, PulseChannelFault := "DB_IO".Inputs.Flow2PulseChannelFault, AnalogChannelFault := "DB_IO".Inputs.Flow2ChannelFault, ValveClosedFb := "DB_IO".Inputs.Valve2Closed, TargetMl := "DB_Recipe".Active.TargetMlCh2, PulsesPerLitre := "DB_Recipe".Active.PulsesPerLitreCh2, UnderToleranceMl := "DB_Recipe".Active.UnderToleranceMl, OverToleranceMl := "DB_Recipe".Active.OverToleranceMl, FlowMaxLMin := 20.0, NoFlowMinLMin := 0.2, PlausibilityPct := 25.0, PulseWindowTimeS := "DB_Recipe".Active.PulseWindowTimeS, NoFlowTimeout := "DB_Recipe".Active.NoFlowTimeout, FillTimeout := "DB_Recipe".Active.FillTimeout, ValveOpenTimeout := "DB_Recipe".Active.ValveOpenTimeout, ValveCloseTimeout := "DB_Recipe".Active.ValveCloseTimeout, PlausibilityTime := "DB_Recipe".Active.PlausibilityTime);
   #DripTimer(IN := (#Coordinator.AutoStep = "E_AutoStep".DRIP_SETTLE), PT := "DB_Recipe".Active.DripSettleTime);
   #Capper(Enable := NOT #immediateStop, RequestEdge := #Coordinator.CapperRequestPulse, Ready := "DB_IO".Inputs.CapperReady, Busy := "DB_IO".Inputs.CapperBusy, Complete := "DB_IO".Inputs.CapperComplete, FaultIn := "DB_IO".Inputs.CapperFault, ResetEdge := #HmiCommands.ResetPulse, AcceptTimeout := T#2s, CompleteTimeout := T#10s);
   IF #Coordinator.VisionRequestPulse AND ("DB_VisionComms".InspectionId < UDINT#4294967295) THEN "DB_VisionComms".InspectionId := "DB_VisionComms".InspectionId + UDINT#1; END_IF;
   // READY low holds VISION_ENABLE low so a cold/restarted edge can atomically
   // seed the PLC session/ID/ACK/heartbeat snapshot before declaring READY.
   "DB_VisionComms".Enable := #processPermissive AND #modelConfigured AND "DB_VisionComms".Ready AND NOT #Vision.Fault; "DB_VisionComms".RecipeId := "DB_Recipe".Active.RecipeId; "DB_VisionComms".ExpectedBottles := 2; "DB_VisionComms".TargetFillLevel := "DB_Recipe".Active.TargetFillLevel;
   #PlcHeartbeatTimer(IN := NOT #PlcHeartbeatTimer.Q, PT := T#500ms);
   IF #PlcHeartbeatTimer.Q THEN
      IF "DB_VisionComms".PlcHeartbeat = UDINT#4294967295 THEN "DB_VisionComms".PlcHeartbeat := UDINT#0;
      ELSE "DB_VisionComms".PlcHeartbeat := "DB_VisionComms".PlcHeartbeat + UDINT#1; END_IF;
   END_IF;
   #Vision(Enable := "DB_VisionComms".Enable, TriggerEdge := #Coordinator.VisionRequestPulse, InspectionId := "DB_VisionComms".InspectionId, SessionEpoch := "DB_VisionComms".SessionEpoch, ExpectedModelId := "DB_VisionComms".ExpectedModelId, ExpectedModelHash := "DB_VisionComms".ExpectedModelHash, Ready := "DB_VisionComms".Ready, Busy := "DB_VisionComms".Busy, Result := "DB_VisionComms".Result, Heartbeat := "DB_VisionComms".Result.Heartbeat, Timeout := "DB_Recipe".Active.VisionTimeout, HeartbeatTimeout := T#1s, ResetEdge := #HmiCommands.ResetPulse);
   "DB_VisionComms".Trigger := #Vision.Trigger;
   IF #modelConfigured THEN "DB_VisionComms".DiagReason := #Vision.DiagReason; ELSE "DB_VisionComms".DiagReason := "E_VisionDiag".MODEL_MISMATCH; END_IF;
   IF #Vision.PublicationAck THEN "DB_VisionComms".ResultAckId := "DB_VisionComms".Result.ResultId; END_IF;
   FOR #i := 0 TO 31 DO #activeFaults[#i] := FALSE; #faultCodes[#i] := 0; END_FOR;
   #activeFaults[0] := NOT "DB_IO".Inputs.SafetyOk; #faultCodes[0] := 1001;
   #activeFaults[1] := NOT "DB_IO".Inputs.GuardClosed; #faultCodes[1] := 1004;
   #activeFaults[2] := NOT "DB_IO".Inputs.AirPressureOk; #faultCodes[2] := 1002;
   #activeFaults[3] := NOT "DB_IO".Inputs.ProductSupplyOk; #faultCodes[3] := 1003;
   #activeFaults[4] := #ConveyorVfd.Fault; #faultCodes[4] := 1101;
   #activeFaults[5] := #PumpVfd.Fault; #faultCodes[5] := 1102;
   #activeFaults[6] := #Gate.Fault; #faultCodes[6] := 1201;
   #activeFaults[7] := #Clamp.Fault; #faultCodes[7] := 1202;
   #activeFaults[8] := #FillCh1.Fault; CASE #FillCh1.DiagReason OF "E_FillDiag".ANALOG_BROKEN_WIRE: #faultCodes[8] := 1307; "E_FillDiag".NO_FLOW: #faultCodes[8] := 1301; "E_FillDiag".PULSE_MISSING: #faultCodes[8] := 1321; "E_FillDiag".ANALOG_NO_FLOW: #faultCodes[8] := 1322; "E_FillDiag".PULSE_ANALOG_DISAGREE: #faultCodes[8] := 1303; "E_FillDiag".UNDERFILL: #faultCodes[8] := 1304; "E_FillDiag".OVERFILL: #faultCodes[8] := 1305; "E_FillDiag".VALVE_OPEN_MISMATCH: #faultCodes[8] := 1308; "E_FillDiag".VALVE_CLOSE_MISMATCH: #faultCodes[8] := 1306; "E_FillDiag".CONTINUED_FLOW: #faultCodes[8] := 1309; ELSE #faultCodes[8] := 1310; END_CASE;
   #activeFaults[9] := #FillCh2.Fault; CASE #FillCh2.DiagReason OF "E_FillDiag".ANALOG_BROKEN_WIRE: #faultCodes[9] := 1317; "E_FillDiag".NO_FLOW: #faultCodes[9] := 1311; "E_FillDiag".PULSE_MISSING: #faultCodes[9] := 1323; "E_FillDiag".ANALOG_NO_FLOW: #faultCodes[9] := 1324; "E_FillDiag".PULSE_ANALOG_DISAGREE: #faultCodes[9] := 1313; "E_FillDiag".UNDERFILL: #faultCodes[9] := 1314; "E_FillDiag".OVERFILL: #faultCodes[9] := 1315; "E_FillDiag".VALVE_OPEN_MISMATCH: #faultCodes[9] := 1318; "E_FillDiag".VALVE_CLOSE_MISMATCH: #faultCodes[9] := 1316; "E_FillDiag".CONTINUED_FLOW: #faultCodes[9] := 1319; ELSE #faultCodes[9] := 1320; END_CASE;
   #activeFaults[10] := #Vision.Fault OR #Vision.HoldRequired OR NOT #modelConfigured OR NOT "DB_VisionComms".Ready;
   IF NOT #modelConfigured THEN #faultCodes[10] := 1506;
   ELSIF NOT "DB_VisionComms".Ready AND NOT #Vision.Fault AND NOT #Vision.HoldRequired THEN #faultCodes[10] := 1501;
   ELSE CASE #Vision.DiagReason OF "E_VisionDiag".READY_TIMEOUT: #faultCodes[10] := 1501; "E_VisionDiag".RESULT_TIMEOUT: #faultCodes[10] := 1502; "E_VisionDiag".RESULT_ID_MISMATCH: #faultCodes[10] := 1503; "E_VisionDiag".QUALITY_BLOCK: #faultCodes[10] := 1504; "E_VisionDiag".HEARTBEAT_LOSS: #faultCodes[10] := 1505; ELSE #faultCodes[10] := 1506; END_CASE; END_IF;
   #activeFaults[11] := #Capper.Fault; IF (#Capper.DiagReason = 1) OR (#Capper.DiagReason = 5) THEN #faultCodes[11] := 1402; ELSE #faultCodes[11] := 1401; END_IF;
   #activeFaults[12] := NOT #HmiCommands.CommunicationsHealthy; #faultCodes[12] := 1601;
   // Quality holds remain alarmed and output-interlocked but are not equipment
   // faults; this preserves the coordinator's INSPECT -> HOLDING disposition path.
   #blockingFault := #immediateStop OR #ConveyorVfd.Fault OR #PumpVfd.Fault OR #Gate.Fault OR #Clamp.Fault OR #FillCh1.Fault OR #FillCh2.Fault OR #Vision.Fault OR NOT #modelConfigured OR NOT "DB_VisionComms".Ready OR #Capper.Fault OR NOT #HmiCommands.CommunicationsHealthy;
   // A restart never reprocesses a bottle already in the cell. Recovery is
   // acknowledged only after the cell is physically empty.
   IF #HmiCommands.ResetPulse AND NOT #blockingFault AND NOT "DB_IO".Inputs.Bottle1Present AND NOT "DB_IO".Inputs.Bottle2Present THEN "DB_IO".PowerRecoveryRequired := FALSE; #processPermissive := NOT #immediateStop; END_IF;
   #Coordinator(InitDone := TRUE, PermissivesOk := #processPermissive, StartEdge := #HmiCommands.StartPulse, StopEdge := #HmiCommands.StopPulse, ResetEdge := #HmiCommands.ResetPulse, AutoRequest := #HmiCommands.AutoPulse, ManualRequest := #HmiCommands.ManualPulse, DispositionRemoved := #HmiCommands.DispositionPulse, PairPresent := "DB_IO".Inputs.Bottle1Present AND "DB_IO".Inputs.Bottle2Present, PairAbsent := NOT "DB_IO".Inputs.Bottle1Present AND NOT "DB_IO".Inputs.Bottle2Present, ConveyorStopped := #ConveyorVfd.Stopped, GateClosed := "DB_IO".Inputs.GateClosed, GateOpen := "DB_IO".Inputs.GateOpen, ClampEngaged := "DB_IO".Inputs.ClampEngaged, ClampReleased := "DB_IO".Inputs.ClampReleased, Fill1Done := #FillCh1.Done, Fill2Done := #FillCh2.Done, DripDone := #DripTimer.Q, VisionAccepted := #Vision.Accepted, VisionPass := #Vision.QualityPass, CapperReady := "DB_IO".Inputs.CapperReady, CapperComplete := #Capper.CompletePulse, BlockingFault := #blockingFault);
   #Alarm(ActiveFaults := #activeFaults, FaultCodes := #faultCodes, AckEdge := #HmiCommands.AckPulse, ResetEdge := #HmiCommands.ResetPulse);
   "DB_HMI".FirstOutAlarm := #Alarm.FirstOutCode;

   // Final physical-output mapping. HMI never writes this structure.
   #outputInterlock := #blockingFault OR #Vision.HoldRequired OR #Coordinator.QualityHold;
   "DB_IO".ReleasePermissive := #processPermissive AND NOT #outputInterlock;
   "DB_IO".Commands.FillValve1 := (#FillCh1.ValveOpenCmd OR #manualValve1Interlocked) AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.FillValve2 := (#FillCh2.ValveOpenCmd OR #manualValve2Interlocked) AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.GateOpen := #Gate.OutToA AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.GateClose := #Gate.OutToB AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.ClampRelease := #Clamp.OutToA AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.ClampEngage := #Clamp.OutToB AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.CapperRequest := #Capper.Request AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.CameraLight := (#Coordinator.AutoStep = "E_AutoStep".INSPECT) AND "DB_IO".ReleasePermissive;
   "DB_IO".Commands.StackGreen := (#Coordinator.State = "E_MachineState".AUTOMATIC) AND NOT #outputInterlock;
   "DB_IO".Commands.StackAmber := (#Coordinator.State = "E_MachineState".HOLDING) OR (#Coordinator.State = "E_MachineState".MANUAL_SETUP);
   "DB_IO".Commands.StackRed := #blockingFault; "DB_IO".Commands.Audible := #Alarm.AnyFault AND NOT #Alarm.Acknowledged;
   %Q0.2 := "DB_IO".Commands.FillValve1; %Q0.3 := "DB_IO".Commands.FillValve2;
   %Q0.4 := "DB_IO".Commands.GateOpen; %Q0.5 := "DB_IO".Commands.GateClose;
   %Q0.6 := "DB_IO".Commands.ClampEngage; %Q0.7 := "DB_IO".Commands.ClampRelease;
   %Q1.0 := "DB_IO".Commands.CapperRequest;
   %Q1.1 := "DB_IO".Commands.StackGreen; %Q1.2 := "DB_IO".Commands.StackAmber; %Q1.3 := "DB_IO".Commands.StackRed; %Q1.4 := "DB_IO".Commands.Audible; %Q1.5 := "DB_IO".Commands.CameraLight;
   IF "DB_IO".ReleasePermissive THEN %QW256 := #ConveyorVfd.ControlWord1; %QW258 := #ConveyorVfd.SpeedSetpointPzd; %QW260 := #PumpVfd.ControlWord1; %QW262 := #PumpVfd.SpeedSetpointPzd;
   ELSE %QW256 := W#16#047E; %QW258 := 0; %QW260 := W#16#047E; %QW262 := 0; END_IF;
   "DB_HMI".StateCode := ENUM_TO_UINT(#Coordinator.State); "DB_HMI".AutoStepCode := ENUM_TO_UINT(#Coordinator.AutoStep); "DB_HMI".QualityHold := #Coordinator.QualityHold OR #Coordinator.DispositionRequired;
END_FUNCTION_BLOCK''',

        "DB_CellMain.scl": f'''// {NOTICE}
DATA_BLOCK "DB_CellMain"
{{ S7_Optimized_Access := 'TRUE' }}
VERSION : 0.1
NON_RETAIN
   "FB_CellMain"
BEGIN
END_DATA_BLOCK''',

        "OB1_Call_Structure.scl": f'''// {NOTICE}
ORGANIZATION_BLOCK "Main"
BEGIN
   "DB_CellMain"();
END_ORGANIZATION_BLOCK''',

        "OB100_Startup.scl": f'''// {NOTICE}
ORGANIZATION_BLOCK "Startup"
BEGIN
   "DB_IO".Commands.FillValve1 := FALSE;
   "DB_IO".Commands.FillValve2 := FALSE;
   "DB_IO".Commands.GateOpen := FALSE;
   "DB_IO".Commands.GateClose := FALSE;
   "DB_IO".Commands.ClampEngage := FALSE;
   "DB_IO".Commands.ClampRelease := FALSE;
   "DB_IO".Commands.CapperRequest := FALSE;
   "DB_IO".Commands.CameraLight := FALSE;
   "DB_IO".Commands.StackGreen := FALSE;
   "DB_IO".Commands.StackAmber := FALSE;
   "DB_IO".Commands.StackRed := FALSE;
   "DB_IO".Commands.Audible := FALSE;
   "DB_IO".ReleasePermissive := FALSE;
   "DB_IO".PowerRecoveryRequired := TRUE;
   IF "DB_VisionComms".SessionEpoch = UDINT#4294967295 THEN "DB_VisionComms".SessionEpoch := UDINT#1;
   ELSE "DB_VisionComms".SessionEpoch := "DB_VisionComms".SessionEpoch + UDINT#1; END_IF;
   "DB_VisionComms".Enable := FALSE;
   "DB_VisionComms".InspectionId := UDINT#0;
   "DB_VisionComms".PlcHeartbeat := UDINT#0;
   "DB_VisionComms".Trigger := FALSE;
   "DB_VisionComms".ResultAckId := UDINT#0;
   "DB_HMI".Start.Request := FALSE;
   "DB_HMI".ControlledStop.Request := FALSE;
   "DB_HMI".Reset.Request := FALSE;
   "DB_HMI".AlarmAck.Request := FALSE;
   "DB_HMI".AutoMode.Request := FALSE;
   "DB_HMI".ManualMode.Request := FALSE;
   "DB_HMI".DispositionRemoved.Request := FALSE;
   "DB_HMI".RecipeApply.Request := FALSE;
   "DB_HMI".ManualConveyorJog.Request := FALSE;
   "DB_HMI".ManualPumpJog.Request := FALSE;
   "DB_HMI".ManualValve1.Request := FALSE;
   "DB_HMI".ManualValve2.Request := FALSE;
   "DB_HMI".ManualSecure.Request := FALSE;
   "DB_Recipe".Apply.Request := FALSE;
   %Q0.2 := FALSE; %Q0.3 := FALSE; %Q0.4 := FALSE; %Q0.5 := FALSE;
   %Q0.6 := FALSE; %Q0.7 := FALSE; %Q1.0 := FALSE; %Q1.1 := FALSE;
   %Q1.2 := FALSE; %Q1.3 := FALSE; %Q1.4 := FALSE; %Q1.5 := FALSE;
   %QW256 := W#16#047E; %QW258 := 0; %QW260 := W#16#047E; %QW262 := 0;
END_ORGANIZATION_BLOCK''',
    }
