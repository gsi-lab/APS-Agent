#!/usr/bin/env python3
"""
AVEVA SimCentral MCP Server
Model Context Protocol server that exposes AVEVA SimCentral tools to AI applications
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP, Context
from tools import schemas, core
from tools.schemas import *
from tools import aveva_tools
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server
mcp = FastMCP("AVEVA SimCentral Server")

# =============================================================================
# SHARED SCHEMAS IMPORTED FROM TOOLS PACKAGE
# =============================================================================

# All Pydantic models are now imported from tools.schemas to avoid duplication
# This ensures consistent data structures across LangGraph and MCP implementations

# =============================================================================
# CONNECTION AND SESSION MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def aps_connect() -> schemas.ConnectionStatus:
    """
    Connect to AVEVA Process Simulation (APS).
    
    This establishes a connection to the AVEVA Process Simulation system and initializes
    all available managers (simulation, model, connector, etc.).
    
    Returns:
        ConnectionStatus: Connection status with open simulations info
    """
    result = core.connect_to_aveva()
    return schemas.ConnectionStatus(**result)


@mcp.tool()
def sim_create(sim_name: str, owner: Optional[str] = None) -> schemas.SimulationInfo:
    """
    Create a new simulation in APS.
    
    Args:
        sim_name: Name for the new simulation
        owner: Owner of the simulation (defaults to current user)
    
    Returns:
        SimulationInfo: Information about the created simulation
    """
    result = core.create_simulation(sim_name, owner)
    return schemas.SimulationInfo(**result)

@mcp.tool()
def sim_open(sim_name: str) -> schemas.SimulationInfo:
    """
    Open an existing APS simulation.
    
    Args:
        sim_name: Name of the simulation to open
    
    Returns:
        SimulationInfo: Result of the open operation
    """
    result = core.open_simulation(sim_name)
    return schemas.SimulationInfo(**result)

@mcp.tool()
def sim_save(sim_name: Optional[str] = None, timeout: Optional[int] = None) -> schemas.OperationResult:
    """
    Save an APS simulation.
    
    Args:
        sim_name: Name of simulation to save (defaults to current simulation)
        timeout: Timeout in milliseconds (optional)
    
    Returns:
        OperationResult: Result of the save operation
    """
    result = core.save_simulation(sim_name, timeout)
    return schemas.OperationResult(**result)

@mcp.tool()
def model_add(
    model_type: str, 
    x: float = 100, 
    y: float = 100, 
    sim_name: Optional[str] = None,
    model_name: Optional[str] = None
) -> schemas.ModelInfo:
    """
    Add a model to the APS simulation.
    
    Args:
        model_type: Type of model to add. Valid options are:
                   • Sources/Sinks: Source, Sink
                   • Heat Exchangers: HeatExchanger  
                   • Separators: Drum, Column
                   • Reactors: CSTR, PFR, Equilibrium
                   • Pumps/Compressors: Pump, Compressor
        x: X position on the flowsheet (default: 100)
        y: Y position on the flowsheet (default: 100)
        sim_name: Target simulation name (defaults to current simulation)
        model_name: Custom name for the model (optional). If provided, model will be renamed after creation.
    
    Returns:
        ModelInfo: Information about the added model
        
    Example:
        add_model("Source", 100, 100, "MySim")  # ✓ Valid - uses default name
        add_model("Source", 100, 100, "MySim", "FeedTank")  # ✓ Valid - custom name
        add_model("Tank", 100, 100, "MySim")    # ✗ Invalid - use "Source" or "Sink"
    """
    result = core.add_model(model_type, x, y, sim_name, model_name)
    return schemas.ModelInfo(**result)

@mcp.tool()
def fluid_create(
    library_name: str,
    fluid_name: str, 
    components: List[str],
    thermo_method: str = "Non-Random Two-Liquid (NRTL)",
    phases: str = "Vapor/Liquid (VLE)",
    databank: str = "System:SIMSCI",
    timeout: int = 30000
) -> schemas.FluidCreationResult:
    """
    Create a new fluid model in APS with the desired components and thermodynamic settings..
    
    Args:
        library_name: Library name (typically same as simulation name)
        fluid_name: Name for the fluid package
        components: List of component names (e.g., ['Water', 'Methanol'])
        thermo_method: Thermodynamic method (default: Non-Random Two-Liquid (NRTL))
        phases: Phase configuration (default: Vapor/Liquid VLE)
        databank: Component databank (default: System:SIMSCI)
        timeout: Timeout in milliseconds (default: 30000)
    
    Returns:
        FluidCreationResult: Result with detailed information about fluid creation,
                           component addition, and thermodynamic configuration
    """
    result = core.create_fluid_complete(library_name, fluid_name, components, 
                                      thermo_method, phases, databank, timeout)
    return schemas.FluidCreationResult(**result)

@mcp.tool()
def fluid_to_source(
    fluid_name: str,
    source_name: str,
    sim_name: Optional[str] = None,
    timeout: int = 30000
) -> schemas.FluidAssignmentResult:
    """
    Set fluid type of one specific source model.
    
    Args:
        fluid_name: Name of the fluid package to assign
        source_name: Name of the source model
        sim_name: Target simulation (defaults to current simulation)
        timeout: Timeout in milliseconds (default: 30000)
    
    Returns:
        FluidAssignmentResult: Result with details about the fluid assignment operation
    """
    result = core.set_fluid_of_source(fluid_name, source_name, sim_name, timeout)
    return schemas.FluidAssignmentResult(**result)

# =============================================================================
# CONNECTION MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def models_connect(from_port: str, to_port: str, sim_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a connection between two model ports and validates that the connection is real.
    
    Args:
        from_port: Source port (e.g., 'SRC1.Out', 'Tank1.Out')
        to_port: Destination port (e.g., 'SNK1.In', 'Pump1.In')  
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        Dict[str, Any]: Result with validation details including success, connection info, 
                       connector_name, stream_flow, and error/suggestion messages
        
    Note:
        - Common port names: '.Out', '.In' for material streams
        - Validation checks for real stream flow properties (e.g., 'S1.F')
        - Phantom connectors (no flow) are automatically removed
        - Returns stream name and flow value for successful connections
    """
    return core.connect_models(from_port, to_port, sim_name)

@mcp.tool()
def var_get_multiple(variables: List[str], sim_name: Optional[str] = None) -> schemas.MultiVariableResult:
    """
    Get values of multiple simulation variables at once.
    
    Args:
        variables: List of variable paths to retrieve
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        MultiVariableResult: Variable values and any errors
    """
    result = core.get_multiple_variables(variables, sim_name)
    return schemas.MultiVariableResult(**result)

@mcp.tool()
def var_set_multiple(variable_data: List[Dict[str, Any]], sim_name: Optional[str] = None) -> schemas.MultiVariableResult:
    """
    Set values of multiple simulation variables at once.
    
    Args:
        variable_data: List of dicts with 'path', 'value', and optional 'unit' keys
            Example: [
                {"path": "SRC1.T", "value": 75.0, "unit": "C"},
                {"path": "SRC1.W", "value": 2}
            ]
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        MultiVariableResult: Operation results including list of successfully changed 
                           variable paths, count, and any errors
    """
    result = core.set_multiple_variables(variable_data, sim_name)
    return schemas.MultiVariableResult(**result)

# =============================================================================
# PARAMETER MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def param_set_multiple(parameter_data: List[Dict[str, Any]], sim_name: Optional[str] = None, timeout: int = 30000) -> Dict[str, Any]:
    """
    Set values of multiple simulation parameters at once.
    
    
    Args:
        parameter_data: List of dicts with 'path' and 'value' keys
            Example: [
                {"path": "Column1.FeedStage[S1]", "value": "7"},
                {"path": "Column1.NStages", "value": "15"},
                {"path": "Column1.Condenser", "value": "Internal"}
            ]
        sim_name: Target simulation name (defaults to current simulation)
        timeout: Timeout in milliseconds (default: 30000)
    
    Returns:
        Dict with batch operation results including:
        - success: Overall success status
        - updated_parameters: Number of successfully updated parameters
        - total_requested: Total number of parameters requested to update
        - results: List of success messages
        - errors: List of error messages (if any)
    """
    return aveva_tools.update_parameters(parameter_data, sim_name, timeout)

# =============================================================================
# SIMULATION STATUS AND MONITORING TOOLS
# =============================================================================

@mcp.tool()
def sim_status(sim_name: Optional[str] = None) -> schemas.SimulationStatus:
    """
    Get input, specification, and convergence status of APS simulation.
    
    Args:
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        SimulationStatus: Detailed status information
    """
    result = core.get_simulation_status(sim_name)
    return schemas.SimulationStatus(**result)

@mcp.tool()
def models_list(sim_name: Optional[str] = None) -> schemas.FlowsheetModelsResult:
    """
    Get detailed information about all models present on the specified APS simulation flowsheet.
    
    Args:
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        FlowsheetModelsResult: Detailed model information including name, type, and description
    """
    result = core.show_models_on_flowsheet(sim_name)
    return schemas.FlowsheetModelsResult(**result)

@mcp.tool()
def connectors_list(sim_name: Optional[str] = None) -> schemas.FlowsheetConnectorsResult:
    """
    Get detailed information about all connectors present on the specified APS simulation flowsheet.
    
    Args:
        sim_name: Target simulation name (defaults to current simulation)
    
    Returns:
        FlowsheetConnectorsResult: Detailed connector information including name, type, 
                                  from_port, to_port, and description
    """
    result = core.show_connectors_on_flowsheet(sim_name)
    return schemas.FlowsheetConnectorsResult(**result)

@mcp.tool()
def model_all_params(sim_name: Optional[str] = None, model_name: Optional[str] = None) -> schemas.ModelParametersResult:
    """
   Get detailed variable information of all parameters of one specific model, including parameter type, current value, units of measurement, and description.
    
    Args:
        sim_name: Target simulation name (defaults to current simulation)
        model_name: Name of the model to query parameters for (required)
    
    Returns:
        ModelParametersResult: Detailed parameter information including name, type, 
                              value, units, and description
    """
    result = core.show_one_model_param(sim_name, model_name)
    return schemas.ModelParametersResult(**result)

@mcp.tool()
def model_all_vars(sim_name: Optional[str] = None, model_name: Optional[str] = None) -> schemas.ModelVariablesResult:
    """
    Get detailed variable information of all variables of one specific model as a flat list.
    
    Each variable includes:
    - name: Variable name
    - specified: Whether variable is specified or calculated
    - value: Current value
    - uom: Unit of measurement
    - description: Variable description (optimized to reference duplicates as "same as xxx" to save tokens)
    
    Args:
        sim_name: Target simulation name (defaults to current simulation)
        model_name: Name of the model to query variables for (required)
    
    Returns:
        ModelVariablesResult: Flat list of all variables with optimized descriptions
    """
    result = core.show_one_model_var(sim_name, model_name)
    return schemas.ModelVariablesResult(**result)




@mcp.prompt()
def create_basic_seperation_flowsheet_fast(
    sim_name: str = "Water_Methanol_Separation",
    component1: str = "Water",
    component2: str = "Methanol",
    # fluid + thermo
    fluid_name: str = "feed",
    thermo_method: str = "Non-Random Two-Liquid (NRTL)",
    phases: str = "Vapor/Liquid (VLE)",
    # models & layout
    source_name: str = "FEED_SRC",
    column_name: str = "COLUMN",
    dist_sink_name: str = "DIST",
    bottoms_sink_name: str = "BOTTOMS",
    source_xy: tuple[int, int] = (100, 100),
    column_xy: tuple[int, int] = (400, 200),
    dist_xy: tuple[int, int] = (600, 100),
    bottoms_xy: tuple[int, int] = (600, 300),
    # feed
    mass_flow_kgph: float = 31653.1,
    pressure_kpa: float = 150.0,
    temperature_K: float = 351.15,
    # fast-settable column variables (set BEFORE connections)
    dp_stage_kpa: float = 2.0,
    contact_fraction: float = 1.0,
    # column parameters to be CONFIRMED/SET before connections
    n_stages: int = 13,
    feed_stage: int = 7,
    condenser_type: str = "Internal",
    reboiler_type: str = "Internal",
    static_head: str = "Include",
    reference_streams: str = "Typical",
    setup_mode: str = "Solve",
) -> str:
    import json

    # Normalize two component inputs
    alias = {
        "h2o": "Water", "water": "Water",
        "meoh": "Methanol", "methanol": "Methanol",
        "etoh": "Ethanol", "ethanol": "Ethanol",
        "ipa": "Isopropanol", "isopropanol": "Isopropanol",
        "acetone": "Acetone"
    }
    def norm(x: str) -> str:
        x0 = (x or "").strip()
        return alias.get(x0.lower(), x0.title())

    c1, c2 = norm(component1), norm(component2)
    components = [v for v in [c1, c2] if v]
    invalid_reason = None
    if len(components) != 2:
        invalid_reason = "Both component1 and component2 must be provided."
    elif components[0].lower() == components[1].lower():
        invalid_reason = "component1 and component2 must be different."

    # Composition defaults
    is_wm = set(map(str.lower, components)) == {"water", "methanol"}
    comp_mode = "KMOL" if is_wm else "MOLFRACTION"

    # Batch variable payload (set BEFORE connections)
    variable_data = [
        {"path": f"{source_name}.W", "value": float(mass_flow_kgph), "unit": "kg/h"},
        {"path": f"{source_name}.P", "value": float(pressure_kpa),   "unit": "kPa"},
        {"path": f"{source_name}.T", "value": float(temperature_K),  "unit": "K"},
        {"path": f"{column_name}.DPstage", "value": float(dp_stage_kpa),     "unit": "kPa"},
        {"path": f"{column_name}.Contact", "value": float(contact_fraction), "unit": "fraction"},
    ]
    if is_wm:
        flows = {"water": 1010.0, "methanol": 420.0}
        for comp in components:
            key = comp.lower()
            if key in flows:
                variable_data.append({
                    "path": f"{source_name}.M[{comp}]",
                    "value": float(flows[key]),
                    "unit": "kmol"
                })
    else:
        for comp in components:
            variable_data.append({
                "path": f"{source_name}.Z[{comp}]",
                "value": 0.5,
                "unit": "fraction"
            })

    variable_data_str = json.dumps(variable_data, ensure_ascii=False)

    def xy(t): return f"({t[0]}, {t[1]})"
    comp_disp = ", ".join(components)

    # Only the tools we actually use in fast mode
    allowed_tools = ["sim_connect", 
    "sim_list", 
    "sim_create",
     "sim_open",
      "sim_save",
       "model_add", 
       "fluid_create", 
       "fluid_assign_to_source",
        "conn_create",
         "var_get_many", 
         "var_set_many", 
         "param_set_many", 
         "sim_status", 
         "model_list", 
         "conn_list", 
         "model_get_parameters", 
         "model_get_variables", 
         "sim_status"]
        

    invalid_guard = (
        f"Inputs invalid: {invalid_reason}. PAUSE and ask the user to provide two distinct component names, then continue."
        if invalid_reason else "Inputs valid."
    )

    # Explicit pre-connection parameter checklist (MUST address before connectors)
    preconn_params_text = (
        f"- COLUMN parameter targets (must be handled BEFORE any connectors):\n"
        f"  • {column_name}.NStages = {n_stages}\n"
        f"  • {column_name}.FeedStage = {feed_stage}\n"
        f"  • {column_name}.Condenser = '{condenser_type}'\n"
        f"  • {column_name}.Reboiler = '{reboiler_type}'\n"
        f"  • {column_name}.StaticHead = '{static_head}'\n"
        f"  • {column_name}.ReferenceStreams = '{reference_streams}'\n"
        "- These are typically PARAMETERS in AVEVA; use update_parameters to set them.\n"
    )

    return f"""
FAST MODE — two components, batched writes, **column parameters handled BEFORE connections**, no cleanup.
Use ONLY these tools: {allowed_tools}

On ANY error or unmet requirement (including add_model name conflicts or write failures):
- **PAUSE and ask the user** with the exact failing path and tool response.
- Offer: (a) fix & retry, (b) skip & continue, (c) abort.

Input validation:
- {invalid_guard}

Target:
- Simulation: "{sim_name}"
- Fluid: "{fluid_name}" with components [{comp_disp}], method "{thermo_method}", phases "{phases}"

Plan:
1) connect_to_aveva
2) Try open_simulation("{sim_name}"); if missing → create_simulation("{sim_name}", owner="Prompt MCP") then open_simulation("{sim_name}")
3) create_fluid_complete(library_name="{sim_name}", fluid_name="{fluid_name}",
   components=[{comp_disp}], thermo_method="{thermo_method}", phases "{phases}")

4) Add models in ONE step each (naming at creation):
   - add_model("Source", {source_xy[0]}, {source_xy[1]}, "{sim_name}", "{source_name}")
   - add_model("Column", {column_xy[0]}, {column_xy[1]}, "{sim_name}", "{column_name}")
   - add_model("Sink", {dist_xy[0]}, {dist_xy[1]}, "{sim_name}", "{dist_sink_name}")
   - add_model("Sink", {bottoms_xy[0]}, {bottoms_xy[1]}, "{sim_name}", "{bottoms_sink_name}")

5)  -set_fluid_of_source(source_name="{source_name}", fluid_name="{fluid_name}")
    - connect_models("{source_name}.Out", "{column_name}.Fin")

6) **PRE-CONNECTION COLUMN PARAMETER SETTINGS (MANDATORY):**
{preconn_params_text}

7) **PRE-CONNECTION VARIABLE WRITES (batched):**
   - set_multiple_variables(variable_data={variable_data_str}, sim_name="{sim_name}")
   - Variables include feed W/P/T, composition ({comp_mode}), and column DPstage/Contact.
   - If any write fails, **PAUSE** and ask the user how to proceed.

8) connect the column to the sinks
   - connect_models("{column_name}.Dout", "{dist_sink_name}.In")
   - connect_models("{column_name}.Lout", "{bottoms_sink_name}.In")

9) **FINAL COLUMN SETUP SWITCH & SOLVE (MANDATORY PAUSE):**
   - PAUSE and instruct the user to set:
       • {column_name}.Setup = '{setup_mode}'
   - Ask the user to let the simulation solve again (or click the appropriate Solve/Run button).
   - Do NOT proceed until the user confirms that the column has re-solved successfully (or reports any issues).

10) save_simulation("{sim_name}")

11) get_simulation_status("{sim_name}") → brief summary (solved/properly_specified/has_required_data)
"""





def main():
    """Main entry point for the AVEVA MCP Server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AVEVA SimCentral MCP Server")
    parser.add_argument("transport", nargs="?", default="stdio", 
                       choices=["stdio", "sse", "streamable-http"],
                       help="Transport protocol (default: stdio)")
    parser.add_argument("--host", default="localhost", help="Host for web transports")
    parser.add_argument("--port", type=int, default=8000, help="Port for web transports")
    
    args = parser.parse_args()
    
    logger.info(f"Starting AVEVA SimCentral MCP Server with {args.transport} transport")
    
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main() 