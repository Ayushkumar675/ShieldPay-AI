# ShieldPay AI: Platform Feature & Usage Guide

Welcome to the exhaustive platform guide for **ShieldPay AI**—an end-to-end parametric micro-insurance platform protecting delivery gig-workers from external income loss factors.

This guide is separated into the two primary platform roles: **Admin** and **Worker**.

---

## 👨‍💼 Administrator Guide

The Admin portal provides comprehensive oversight of the platform's liquidity, risk thresholds, detected fraud rings, and active systemic disruptions. 

### 1. Admin Dashboard (`/admin`)
The central command center for financial health and aggregated risk forecasting.

- **Stat Cards**: Displays Total Premiums Collected, Total Payouts, Liquidity Ratio, Active Fraud Alerts, Total Claims, and the platform Reserve Balance.
- **Premium vs Payout Flow (Area Chart)**: Tracks the trailing 12-week trajectory of premiums collected versus automatic payouts distributed. Use this to determine if platform pricing models need adjustment.
- **Claims Distribution (Pie Chart)**: Breaks down claims by their AI-adjudicated status (`Auto Approved`, `Soft Verify`, `Delayed Review`, etc.).
- **Fraud Alert Heatmap (AI-Powered)**: Groups all historical fraud alerts by city, showing you precisely which operating zones are exhibiting high-risk behavior based on severity mapping.
- **High-Risk Warehouse Zones**: Ranks logistics warehouses by their assigned worker's aggregate "reliability scores", helping admins proactively isolate bad clusters.

### 2. Fraud Intelligence Panel
A dedicated space to monitor the 5-Layer Defense Model.

- **5-Layer Defense Status**: A graphical breakdown indicating exactly where the system is flagging the highest concentration of risk *(Movement, Delivery Activity, Environmental Check, Device Integrity, Graph ML)*.
- **Detected Fraud Rings**: Displays live fraud networks isolated by the AI's spatial clustering logic. It identifies workers who exhibit identical GPS anomalies simultaneously.
- **Recent Fraud Alerts**: A constant active feed of system-wide alarms for actions like "GPS Spoofing", "Emulator Detection", or "Temporal Claim Spikes".

### 3. Disruption Monitor 
A feed of external systemic triggers (weather, traffic spikes).

- **"Simulate Disruption" (Button)**: *Developer/Demo Tool*. Allows you to manually trigger an API blast simulating a major event (e.g., Heavy Rainfall, Traffic Crash) in a designated city. When triggered, the backend `ClaimEngineService` catches the pulse, instantly identifies any workers operating in that city, computes their income loss, and automatically queues payouts within 500ms.
- **"Clear All" (Button)**: Removes all inactive disruptions from the active UI feed.

### 4. Claims Sandbox
An overview of all claims dynamically flowing through the system.

- **"Confirm Claim" (Button/Action)**: If a claim was pushed to the `Delayed Review` state due to a worker possessing a low Trust Score `< 0.50`, an admin can manually click Confirm to release the funds. 

---

## 🚴 Worker Guide

The Worker portal provides gig-workers absolute transparency regarding their income protection, risk forecasts, and intelligent trust scores.

### 1. Worker Dashboard (`/worker`)
The main interface answering three questions: "Am I covered?", "What's my risk this week?", and "How deeply does the platform trust me?"

- **Stat Cards**: Displays Weekly Insured Income, Trust Score tier, Total Claims, and Current AI Risk Level.
- **Logistics Risk vs Parcels (7 Days)**: An AI-Projected forecast displaying expected job volume (Parcels) against environmental disruption Risk for the upcoming week. It helps workers visually prepare for challenging conditions.
- **Income Forecast vs Normal**: A Bar Chart comparing exactly how much money the worker *should* make over the next 4 weeks versus what the AI predicts they *will* make when accounting for historical weather/traffic delays in their zone.
- **Trust Score Breakdown**: Shows the 5 underlying metrics defining their `Trust Score`. Moving carefully, maintaining active deliveries, passing emulator checks, and avoiding claim spikes keeps these bars green.
  - **Why it matters**: 
    - `≥ 85%`: Claims auto-approve and payout via UPI instantly.
    - `50-85%`: Requires "Soft Validation" (e.g., uploading a photo).
    - `< 50%`: Funds are frozen for 24-48 hours pending manual admin review.

### 2. My Policies
- **Active Coverage Listing**: Shows the worker's base premium cost per week against their total coverage ceiling. 
- **Purchase Premium (Button)**: Allows the worker to buy into the insurance pool. (Currently mocked integration).

### 3. Claiming Process
Unlike traditional insurance spanning weeks of paperwork, ShieldPay AI workers **do not manually file claims**. 
- If a flood hits their city, the Admin/System triggers the event via the systemic API.
- The Worker Dashboard instantly updates via real-time hooks stating: *"Incoming Disbursement. Expected Loss Detected."*
- Funds are transferred with zero forms required!

---

## 🛠 Simulated Testing (How to utilize the platform)

Because this platform requires external events (like real storms) to automate payouts, we have built simulation features.

**To Run a Test Flow:**
1. Login with a Worker Account and view the dashboard (observe your Trust Score and zero claims).
2. Login to the Admin Account on a separate browser window or incognito.
3. Navigate to **Disruptions** on the Admin side and utilize the **Simulate Disruption** tool.
4. Select the Worker's active city (e.g., *Mumbai*).
5. The backend AI models will rapidly score the event, isolate the worker, and approve the claim. 
6. Refresh the Worker Dashboard: The new Income Loss Claim will be visible instantly in the Recent Claims table!
