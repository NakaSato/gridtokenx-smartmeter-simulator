from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .dependencies import get_engine

router = APIRouter(prefix="/api/vpp", tags=["VPP"])

@router.get("/clusters")
async def get_vpp_clusters(engine=Depends(get_engine)):
    """Get status of all VPP clusters"""
    return {
        "success": True,
        "clusters": engine.vpp.get_all_cluster_statuses()
    }

class VPPDispatchRequest(BaseModel):
    cluster_id: str
    target_kw: float

@router.post("/dispatch")
async def dispatch_vpp(request: VPPDispatchRequest, engine=Depends(get_engine)):
    """Dispatch a VPP cluster to a target power (kW)"""
    try:
        carbon_intensity = None
        if engine.net:
             ext_grid_p = engine.net.res_ext_grid.p_mw.sum() if hasattr(engine.net, 'res_ext_grid') else 0.0
             total_p_cons = engine.net.res_load.p_mw.sum() if hasattr(engine.net, 'res_load') else 1.0
             carbon_intensity = (ext_grid_p / total_p_cons) * 500.0 if total_p_cons > 0 else 0.0

        dispatches = engine.vpp.dispatch_cluster(
            request.cluster_id, 
            request.target_kw,
            carbon_intensity=carbon_intensity
        )
        
        applied_count = 0
        for m_id, kw in dispatches.items():
            m_obj = next((m for m in engine.meters if m.meter_id == m_id), None)
            if m_obj:
                m_obj.receive_dispatch(kw)
                applied_count += 1
                
        return {
            "success": True,
            "details": {
                "meters_dispatched": applied_count,
                "dispatches": dispatches
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
