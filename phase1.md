# Phase 1: Initial Architecture & Prototype Framework (What Was There)

Phase 1 encompasses the state of the ShieldPay AI micro-insurance platform prior to our recent production migrations. The system existed as a brilliant but localized engineering prototype designed to demonstrate the feasibility of AI-driven, zero-paperwork parametric insurance for gig-workers. 

## Architectural Foundation
- **Frontend Layer**: Built using React + Vite. Provided a robust structural interface via lucide-react icons and rich Recharts components (Line, Bar, Area visualizations). Dedicated layouts for workers and administrators.
- **Backend Service (Brain)**: A FastAPI orchestrator (`main.py`) powered entirely by Python asynchronous routing, directly linked to a MongoDB schema utilizing Motor.
- **AI/ML Pipeline**: Consisted of XGBoost models (Risk Engine, Income Forecast) and Isolation Forests (Fraud Detection), stored natively, to probabilistically map out when a worker was caught in a disruption (Flood/Traffic) and simultaneously gauge their "Trust Score".

## Identified Limitations & Constraints 
While the backend processed active disruption events effectively, the platform harbored distinct scaling vulnerabilities:
1. **Mock Data Reliance**: Instead of pulling live MongoDB aggregations, complex UI features (like 7-Day Risk Projections or Fraud Heatmaps) actively utilized hardcoded data arrays (`demoProfiles`) embedded directly within the `.jsx` component mounts.
2. **Local Networking Trap**: The frontend securely assumed it was polling `localhost:8000`. Running cross-origin tasks without Nginx reverse proxying inherently triggered crippling CORS blocking in cloud environments.
3. **Execution Monoliths**: 
   - Operated purely on bare-metal `uvicorn`. No worker distribution.
   - The disruption scanner `APScheduler` was locked within the primary application execution thread, guaranteeing race conditions and duplication events if scaled across multiple instances.
4. **No Orchestration**: Deploying the stack required navigating split terminals manually; there were no container environments to isolate dependencies or enforce reproducible builds securely.
