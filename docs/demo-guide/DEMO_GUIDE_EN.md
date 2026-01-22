# LinkC Smart Cleaning Robot Management Platform - MVP Demo Guide

**Version**: 1.0
**Date**: January 2026
**Classification**: Internal Use

---

## Table of Contents

1. [Demo Preparation](#1-demo-preparation)
2. [Demo Flow](#2-demo-flow)
3. [Scenario-Based Demo Scripts](#3-scenario-based-demo-scripts)
4. [Talking Points for Different Audiences](#4-talking-points-for-different-audiences)
5. [FAQ Responses](#5-faq-responses)
6. [Technical Backup Plans](#6-technical-backup-plans)

---

## 1. Demo Preparation

### 1.1 Environment Checklist

| Item | Action | Expected Result |
|------|--------|-----------------|
| Network | Access demo URL | Page loads normally |
| Backend | Check /health endpoint | Returns healthy |
| Demo Data | Call initialization API | Data ready |
| Browser | Use Chrome/Edge | Full screen mode |
| Backup | Prepare screen recording | Ready to switch |

### 1.2 Demo Environment URLs

| Service | URL |
|---------|-----|
| Executive Dashboard | http://[SERVER_IP]:5173/executive |
| Operations Console | http://[SERVER_IP]:5173/operations |
| Live Map | http://[SERVER_IP]:5173/demo/map |
| Mobile View | http://[SERVER_IP]:5173/mobile |
| API Docs | http://[SERVER_IP]:8000/docs |

### 1.3 Five Minutes Before Demo

```
1. Open all demo page tabs
2. Initialize data: POST /api/v1/demo/init
3. Start simulation: POST /api/v1/simulation/start
4. Confirm robots are moving on the map
5. Clear browser notifications/popups
6. Close unrelated applications
```

---

## 2. Demo Flow

### 2.1 Standard Demo Flow (15 minutes)

```
┌─────────────────────────────────────────────────────────────┐
│  Opening (1 minute)                                          │
│  "Welcome to LinkC, the next-generation human-machine        │
│   collaboration platform for cleaning management"            │
├─────────────────────────────────────────────────────────────┤
│  Scene 1: Executive View - Strategic Dashboard (3 min)       │
│  Show: KPI Overview → Cost Savings → Multi-Building Mgmt     │
├─────────────────────────────────────────────────────────────┤
│  Scene 2: Operations View - Real-time Monitoring (5 min)     │
│  Show: Map Monitoring → Task Scheduling → Alert Handling     │
├─────────────────────────────────────────────────────────────┤
│  Scene 3: AI Collaboration - Intelligent Decisions (4 min)   │
│  Show: Natural Language → Agent Reasoning → Human Approval   │
├─────────────────────────────────────────────────────────────┤
│  Scene 4: Mobile Experience (2 min)                          │
│  Show: Alert Push → Field Response → Quick Actions           │
├─────────────────────────────────────────────────────────────┤
│  Summary & Vision (1 minute)                                 │
│  "LinkC is defining the future of human-machine collaboration│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Quick Demo Flow (5 minutes)

Suitable for: Elevator pitch, trade show quick intro

```
1. Executive Dashboard (1 min) - Show core KPIs
2. Live Map (2 min) - Show robot movement
3. AI Dialog (1.5 min) - Show intelligent scheduling
4. Summary (0.5 min) - Emphasize value proposition
```

---

## 3. Scenario-Based Demo Scripts

### Scene 1: Executive Dashboard

**Page**: /executive

**Steps**:
1. Show health score card (92 points)
2. Scroll through core KPIs
3. Click into data analytics
4. Show cost comparison charts

**Script**:

> "This is LinkC Executive Dashboard, providing leadership with a comprehensive operational overview at a glance.
>
> The 92-point health score you see is calculated in real-time by our AI system, considering task completion rates, equipment status, energy efficiency, and multiple other dimensions.
>
> Core KPIs are crystal clear:
> - **96.8% Task Completion Rate** - Far exceeding the industry average of 85%
> - **35% Cost Reduction** - Saving over $60,000 monthly
> - **87% Robot Utilization** - The result of intelligent scheduling
>
> This is not just data visualization - it is an AI-driven decision support system."

**Key Data Points**:
- Task Completion Rate: 96.8%
- Monthly Cost Savings: $60,000+
- Robot Utilization: 87.2%
- Customer Satisfaction: 4.8/5.0

---

### Scene 2: Real-time Map Monitoring

**Page**: /demo/map

**Steps**:
1. Show robots moving in real-time
2. Click to select a working robot
3. Show robot detail panel
4. Toggle heatmap view
5. Demo zoom and floor switching

**Script**:

> "This is our real-time monitoring center. Each icon represents a cleaning robot working right now.
>
> [Click robot] This is Robot A-01, currently executing a lobby cleaning task, 85% battery, 72% task progress.
>
> [Toggle heatmap] The heatmap shows cleaning frequency by area - darker colors indicate higher cleaning demand. Our AI uses this data to intelligently assign tasks.
>
> Data updates every 500 milliseconds, ensuring you always have real-time visibility."

**Interaction Tips**:
- Let the audience select a robot
- Demo zooming to a specific area
- Show robot path planning

---

### Scene 3: AI Intelligent Scheduling

**Page**: /trainer (Training Workbench)

**Steps**:
1. Enter natural language command: "Schedule lobby area cleaning"
2. Show AI reasoning process
3. Show recommended solution
4. Demo confirm/modify workflow

**Script**:

> "Now let us see LinkC core capability - AI intelligent scheduling.
>
> [Enter command] I will use natural language: 'Schedule lobby area cleaning'
>
> [Show reasoning] Watch the AI thinking:
> 1. Analyze request → Identified as cleaning task
> 2. Query available robots → Found A-02 and A-05 available
> 3. Evaluate best option → A-02 is closer with better battery
>
> [Show result] AI recommends dispatching Robot A-02, estimated 15 minutes to complete.
>
> This is the essence of human-machine collaboration - AI handles analysis and recommendations, humans make decisions and maintain oversight. We believe this is the right way to apply AI."

**Key Messages**:
- Demonstrate AI reasoning transparency
- Emphasize humans retain final decision authority
- Highlight efficiency gains (from 5-minute decisions to 5-second recommendations)

---

### Scene 4: Mobile Response

**Page**: /mobile

**Steps**:
1. Show mobile monitoring homepage
2. Trigger a low battery alert
3. Show alert details
4. Demo quick response actions

**Script**:

> "Finally, let us see how field personnel use LinkC.
>
> [Show homepage] The mobile interface is designed for on-site work - large fonts, big buttons, critical information first.
>
> [Trigger alert] The system just detected Robot A-03 with battery below 20%, automatically triggering an alert.
>
> [Handle alert] Field staff can one-click recall for charging, or view detailed status for manual handling.
>
> From alert to resolution, average response time dropped from 15 minutes to 2 minutes."

---

## 4. Talking Points for Different Audiences

### 4.1 Investors/Executives (Focus: ROI & Market)

**Core Message**: LinkC is the frontrunner in the intelligent cleaning management space

**Opening**:
> "Property cleaning is a $50 billion market undergoing intelligent transformation. LinkC is not just management software - it is the operating system for the human-machine collaboration era."

**Key Data**:
- Market Size: $50B+ global property cleaning market
- Cost Reduction: 35% operational cost savings
- Efficiency Gain: 40% cleaning efficiency improvement
- Customer Satisfaction: 4.8/5.0

**Vision Statement**:
> "Our vision is to become the infrastructure for the human-machine collaboration era. Today it is cleaning robots, tomorrow it is security robots, delivery robots. LinkC will be the bridge connecting humans and machines."

**Competitive Advantages**:
1. **AI-Native**: Not AI added to traditional software, but AI-driven design
2. **Human-Machine Collaboration**: Humans retain decision authority, AI handles analysis
3. **Open Platform**: Supports multi-brand robot integration
4. **Data Flywheel**: Gets smarter with use

---

### 4.2 Property Executives (Focus: Cost & Efficiency)

**Core Message**: LinkC helps you reduce costs and improve quality

**Opening**:
> "I understand your challenges - rising labor costs, hiring difficulties, inconsistent service quality. LinkC was built to solve these problems."

**Pain Point Resonance**:
- Labor costs rising 10-15% annually
- Cleaning staff turnover rate up to 40%
- Service quality hard to standardize
- Customer complaints difficult to trace

**Solution**:
> "With LinkC:
> - Human-machine collaboration: 1 person can manage 5-8 robots
> - Smart scheduling: Reduces idle time and redundant cleaning
> - Full documentation: Service quality is traceable
> - Data-driven: Continuously optimize cleaning plans"

**ROI Calculation**:
> "For a 100,000 sqm commercial complex:
> - Traditional: 20 cleaners × $800/month = $16,000/month
> - LinkC: 8 robots + 5 staff = $10,500/month
> - **Monthly savings: $5,500, Annual savings: $66,000**"

---

### 4.3 Operations Managers (Focus: Usability)

**Core Message**: LinkC makes your work easier

**Opening**:
> "How many calls do you handle daily? How many scheduling issues do you coordinate? LinkC can reduce 80% of your coordination work."

**Feature Highlights**:
- Real-time monitoring: Full visibility on one screen
- Smart scheduling: Reduces manual coordination
- Auto alerts: Catch problems early
- Mobile office: Handle issues anywhere

**Use Case**:
> "Morning at the office, open LinkC dashboard - last night cleaning report is ready.
>
> One robot needs maintenance - the system has already scheduled a replacement.
>
> Got a last-minute meeting room cleaning request? Say one sentence to the AI, task dispatched.
>
> This is your day with LinkC."

---

### 4.4 Technical Decision Makers (Focus: Architecture)

**Core Message**: LinkC is a technically advanced human-machine collaboration platform

**Opening**:
> "LinkC features AI-native architecture design, built on the latest large language model technology, achieving true human-machine collaboration."

**Technical Highlights**:
- **Architecture**: Microservices + MCP Protocol + Agent Architecture
- **AI**: Claude/GPT-based intelligent decision engine
- **Real-time**: WebSocket push, <500ms latency
- **Extensibility**: Multi-brand robots, multi-device types
- **Security**: Enterprise-grade permissions, data encryption

**Integration Capabilities**:
> "LinkC easily integrates with your existing IT systems:
> - Property Management Systems (PMS)
> - Building Management Systems (BMS)
> - Enterprise SSO (LDAP/OAuth)
> - Third-party Robot APIs"

**API Example**:
> "All features have API support. You can build your own applications on LinkC. For example, this task scheduling API..."

---

## 5. FAQ Responses

### 5.1 Product Related

**Q: Which robot brands does LinkC support?**
> A: The MVP version deeply integrates with Gaussian robots. Our open architecture supports rapid integration of other brands. Ecovacs, Pudu, and other mainstream brands are being integrated, expected Q2 completion.

**Q: Will the AI make mistakes?**
> A: Great question. LinkC design philosophy is "AI suggests, humans decide." AI analyzes data and provides recommendations, but critical operations require human confirmation. This maximizes AI efficiency while ensuring safety and control.

**Q: How is data security ensured?**
> A: Three-layer protection: 1) On-premise deployment option; 2) Enterprise-grade encrypted transmission; 3) Fine-grained access control. We can customize solutions based on your security requirements.

### 5.2 Business Related

**Q: What is the pricing?**
> A: We offer flexible pricing models:
> - SaaS subscription: Per-robot pricing
> - Private deployment: One-time license + annual maintenance
> Specific pricing depends on your scale; our sales team can discuss details.

**Q: How long is implementation?**
> A: Standard implementation is 2-4 weeks:
> - Week 1: Requirements confirmation, environment deployment
> - Week 2: Data integration, system configuration
> - Weeks 3-4: Training, trial run, optimization

**Q: Do you have success cases?**
> A: We are conducting POC validation with several leading property companies, including [mentionable partners]. Feedback has been very positive; we expect formal commercial cases in Q2.

### 5.3 Technical Related

**Q: What network environment is required?**
> A: Basic requirements:
> - Stable internet connection (4G/5G/WiFi)
> - Robots on the same LAN
> - Recommended bandwidth: 5Mbps+ upload

**Q: Can it be deployed on-premise?**
> A: Absolutely. We support three deployment models:
> 1. Public cloud SaaS
> 2. Private cloud deployment
> 3. Hybrid cloud solution

---

## 6. Technical Backup Plans

### 6.1 Network Issues

**Symptom**: Slow page load or unable to load

**Resolution**:
1. Switch to backup network (mobile hotspot)
2. Use offline demo video
3. Show screenshot PPT

### 6.2 Service Anomaly

**Symptom**: API returns errors

**Resolution**:
1. Refresh page and retry
2. Reset demo data: `POST /api/v1/demo/reset`
3. Switch to backup demo environment

### 6.3 Demo Data Issues

**Symptom**: Abnormal data display

**Resolution**:
1. Reinitialize: `POST /api/v1/demo/init`
2. Switch scenario: `POST /api/v1/demo/scenario`
3. Use pre-recorded video instead

### 6.4 Backup Materials Checklist

- [ ] Demo video (15-min full version)
- [ ] Demo video (5-min condensed version)
- [ ] Screenshot PPT (20 slides)
- [ ] Product brochure PDF
- [ ] Backup demo environment URL

---

## Appendix: Demo Checklist

### Day Before Demo
- [ ] Confirm demo environment accessible
- [ ] Prepare backup network solution
- [ ] Check backup materials completeness
- [ ] Confirm demo duration and audience

### 1 Hour Before Demo
- [ ] Test all demo pages
- [ ] Initialize demo data
- [ ] Start simulation engine
- [ ] Close unrelated apps and notifications

### 5 Minutes Before Demo
- [ ] Open all tabs
- [ ] Confirm robots are moving
- [ ] Adjust browser to full screen
- [ ] Take a deep breath, ready to start!

---

*Document Version: 1.0*
*Last Updated: January 2026*
*LinkC Team - Defining the Future of Human-Machine Collaboration*
