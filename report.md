# ShieldPay AI: Project & Development Context Report

## 1. Project Overview
**ShieldPay AI** is an end-to-end intelligent parametric micro-insurance platform designed specifically for e-commerce delivery and gig-economy workers. It automatically protects workers from income loss caused by external factors such as extreme weather, city-wide traffic disruptions, demand crashes, and operational anomalies. The core value proposition is **instant, AI-adjudicated, zero-friction claims** triggered autonomously by systemic data feeds.

## 2. Technical Architecture

### Frontend (React/Vite)
- A dynamic, event-driven web application featuring dedicated portals:
  - **Worker Dashboard**: Real-time policy status, active coverage, trust scores, and claims history.
  - **Admin Dashboard**: Platform liquidity metrics, financial trends, and overarching health.
  - **Disruption Monitor**: A live feed of systemic events (e.g., weather warnings, traffic spikes).
  - **Fraud Intelligence Panel**: Heatmaps and alerts detecting GPS spoofing and organized fraud rings.
  - **Claims Engine**: Tracking payout stages (Instant, Soft-Verify, Delayed).

### Backend (FastAPI - Python)
- A highly concurrent microservices ecosystem built to manage the insurance lifecycle:
  - **ClaimEngineService**: The orchestration brain. Receives disruption feeds, filters active policies, queues AI risk and fraud models, assigns payout tiers, triggers disbursements, and logs system state.
  - **LiquidityEngine**: Constantly tracks total premiums collected, payouts disbursed, and calculates the platform's reserve ratio to predict solvency against future claims. 
  - **Scheduler**: Automates weekly financial aggregation and continuous disruption scanning.

### AI / Machine Learning Pipeline
- Pre-trained and joblib-pickled scikit-learn models executed at runtime:
  - **Risk Engine** (XGBoost): Calculates base risk given location and historical worker activity.
  - **Income Forecast** (XGBoost Regression): Predicts expected daily wage loss for a worker based on the severity of a disruption trigger.
  - **Fraud Detector** (Isolation Forest): Continuously evaluates worker behavior patterns and telemetry to isolate suspicious activities and potential "fraud rings".
  - **Trust Scorer**: Computes a continuous `0 - 1.0` trustworthiness benchmark that determines if a worker receives an instant auto-approved payout or a delayed manual review.

### Database (MongoDB)
- Designed to utilize non-relational, high-throughput asynchronous document storage via the `motor` driver. 
- **Collections**: `users`, `policies`, `claims`, `disruptions`, `fraud_alerts`, `payouts`, `platform_metrics`.

---

## 3. Development Journey & Refactoring Roadmap

This project originated as a hackathon prototype relying heavily on in-memory mock datasets and seeded JSON endpoints. The central objective of this development phase was to transition the prototype into a fully persistent, production-ready backend service.

### Phased Execution:
- **Phase 1: Claim Automation Engine** 
    - Migrated the manual API endpoint logic into a robust `ClaimEngineService.process_disruption_event()` pipeline.
- **Phase 2: Persistent Data Models** 
    - Wired up MongoDB collections. Defined strictly typed Pydantic Schemas mapping directly into Document DB writes.
- **Phase 3: Financial Liquidity Engine** 
    - Standardized how the platform tracks its money. Premium purchases incrementally raise the `reserve_balance`, while instantaneous claim payouts automatically debit it. 
- **Phase 4: Frontend Data Plumbing** 
    - Purged all hard-coded mock arrays from the React `.jsx` components. Directed all fetch calls to the live FastAPI routers.
- **Phase 5: Real Simulation Pipeline** 
    - Constructed test endpoints (`/simulate-disruption`, `/simulate-fraud-cluster`) capable of injecting synthetic disruption parameters directly into the live `ClaimEngineService` logic to evaluate the AI pipeline output.
- **Phase 6: Event-Driven Frontend Refresh** 
    - Re-architected `api.js` to dispatch global refresh events to React `useEffect` hooks, allowing the dashboard UI to live-reload whenever a simulation successfully commits a backend change.
- **Phase 7: Weekly Financial Trends** 
    - Deprecated the in-memory array generators and wrote historical MongoDB aggregations to compute trailing 12-week metrics.
- **Phase 8: System Verification** 
    - Standardized error handling and applied structural runtime loggers throughout the state machines.

---

## 4. Crucial Engineering Hurdles & Bug Fixes

While migrating the system, several deep-rooted framework compatibility issues emerged, requiring extensive codebase patching:

1. **Motor v3.3 API Deprecations (`NotImplementedError`)**
   - **Issue:** The legacy codebase heavily relied on MongoDB attribute access (e.g., `db.users.find()`). Upgraded versions of the Motor driver removed this feature, breaking the entire backend.
   - **Resolution:** A global Python string-replacement script was utilized to safely migrate the entire repository to Python dictionary bracket syntax (e.g., `db["users"].find()`).
2. **Pydantic Schema Mismatches**
   - **Issue:** Cross-referencing bugs emerged where older imports attempted to use `Payment` and `Disruption` schemas, while the updated models were named `Payout` and `DisruptionTrigger`.
   - **Resolution:** Traced the Uvicorn stack traces and retroactively patched the service imports to reflect the single-source-of-truth schemas.
3. **PowerShell Unicode Panics (`cp1252` encoding)**
   - **Issue:** Windows PowerShell background jobs crashed the FastAPI daemon entirely because of hard-coded standard-output emojis (e.g., 🧠, ✅) which threw fatal `UnicodeEncodeError` exceptions on boot. 
   - **Resolution:** Stripped all unicode symbols from the `print()` startup statements in `main.py` and `ai_routes.py`.
4. **Zero-Byte File Truncation Data Loss**
   - **Issue:** An aggressive python regex pipeline inadvertently wiped several `.py` files due to synchronous OS file-lock race conditions.
   - **Resolution:** Initialized a `git checkout .` to attempt a rollback. For untracked/uncommitted components, successfully injected the lost file contents entirely from the Chat Context Memory.
5. **The Final Blocker: Uvicorn Startup Thread Deadlocks**
   - **Issue:** Currently, launching the FastAPI server will hang silently and refuse all incoming connections on port 8000. 
   - **Root Cause:** A `ServerSelectionTimeoutError`. The FastAPI `lifespan` runs `await connect_db()` which forces MongoDB indexing (`create_index()`). Because a local `mongod` instance is not actively running on the user's OS at port `27017`, the Motor async driver locks the main thread for its 30-second default timeout duration, trapping all endpoint routers.
   - **Next Steps:** The user must install and launch the MongoDB Community Daemon locally, or provide an external MongoDB Atlas configuration URI via a `.env` file to fully bridge the connection.
