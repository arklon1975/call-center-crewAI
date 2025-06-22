# Call Center System - Project Documentation

## Overview
Multi-Agent Call Center System built with CrewAI and FastAPI. Features specialized AI agents for customer service, call routing, and supervision with comprehensive authentication and role-based access control.

## Current Status
- ✅ Application running successfully on port 5000
- ✅ Database initialized with SQLite
- ✅ Authentication system working
- ✅ All core modules functional

## Default Credentials
- **Username:** admin
- **Password:** Admin123!
- **Role:** Administrator (full access)

## Project Architecture

### Core Components
- **FastAPI Server:** Main application with authentication middleware
- **CrewAI Agents:** Customer service, call routing, and supervisor agents
- **SQLite Database:** User management and call data storage
- **Authentication:** JWT-based with role-based access control

### Key Features
- Multi-agent AI system for call handling
- Real-time dashboard for monitoring
- Role-based access (Admin, Supervisor, Agent)
- Call routing and queue management
- Performance analytics and reporting

## Recent Changes
- **2025-06-22:** Implemented complete logout functionality with user dropdown menu
- **2025-06-22:** Added password change functionality in user interface
- **2025-06-22:** Fixed missing fastapi-mail dependency and router initialization
- **2025-06-22:** Enhanced navbar with user menu and session management

## User Preferences
- Language: Spanish/English bilingual support
- Authentication: Prefers simple username/password login
- Interface: Expects functional dashboard with real-time updates

## Technical Notes
- BCrypt warning is cosmetic only - authentication fully functional
- Server binds to 0.0.0.0:5000 for Replit compatibility
- Debug mode enabled in development environment