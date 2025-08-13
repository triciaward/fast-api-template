# 🌐 Frontend AI Development with Enhanced .cursorrules

**Leverage your optimized AI system for efficient full-stack development!**

This guide shows how to extend your AI-optimized FastAPI template to include frontend development while maintaining the same efficiency and quality standards.

## 🎯 **What You'll Learn**

- **How AI adapts** to frontend development
- **Maintaining efficiency** across full-stack development
- **Frontend-specific patterns** and conventions
- **Integration strategies** between frontend and backend
- **Cost optimization** for full-stack development

## 🚀 **How Your Enhanced .cursorrules Handle Frontend**

### **Current Backend Efficiency:**
- **Cache usage**: 99.1% (79,150 tokens from cache)
- **Cost reduction**: 75-80% compared to default
- **Project knowledge**: AI understands your 173 test files and patterns

### **Frontend Development Evolution:**
- **Phase 1**: Learning new patterns (higher token usage)
- **Phase 2**: Established conventions (lower token usage)
- **Phase 3**: Full-stack efficiency (optimal token usage)

## 📁 **Frontend Project Structure**

### **Recommended Organization:**
```
fast-api-template/
├── app/                        # Backend (cached, efficient)
├── frontend/                   # Frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/             # Page-level components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API integration services
│   │   ├── utils/             # Frontend utilities
│   │   ├── styles/            # Global styles and themes
│   │   └── types/             # TypeScript type definitions
│   ├── public/                # Static assets
│   ├── package.json           # Dependencies and scripts
│   └── tsconfig.json          # TypeScript configuration
├── docs/tutorials/            # Backend guides (cached)
├── docs/frontend/             # Frontend-specific guides
└── .cursorrules               # AI optimization rules
```

### **Integration Points:**
- **API endpoints** - Connect to your FastAPI backend
- **Authentication** - Use JWT tokens from backend
- **Data models** - Mirror backend schemas in TypeScript
- **Error handling** - Consistent patterns across stack

## 🔧 **Setting Up Frontend Development**

### **1. Initialize Frontend Project:**
```bash
# Create frontend directory
mkdir frontend
cd frontend

# Initialize React with TypeScript
npx create-react-app . --template typescript

# Or use Vite for faster development
npm create vite@latest . -- --template react-ts
```

### **2. Install Essential Dependencies:**
```bash
# Core dependencies
npm install axios react-router-dom @tanstack/react-query

# UI components (choose one)
npm install @mui/material @emotion/react @emotion/styled
# OR
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion

# Form handling
npm install react-hook-form @hookform/resolvers zod

# State management
npm install zustand
# OR
npm install @reduxjs/toolkit react-redux
```

### **3. Configure API Integration:**
```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

## 🎨 **Frontend Development Patterns**

### **Component Structure:**
```typescript
// src/components/FeatureName/FeatureName.tsx
import React from 'react';
import { useFeature } from './useFeature';
import { FeatureForm } from './FeatureForm';
import { FeatureList } from './FeatureList';

interface FeatureNameProps {
  // Props interface
}

export const FeatureName: React.FC<FeatureNameProps> = (props) => {
  const { features, createFeature, isLoading } = useFeature();

  return (
    <div className="feature-name">
      <FeatureForm onSubmit={createFeature} />
      <FeatureList features={features} isLoading={isLoading} />
    </div>
  );
};
```

### **Custom Hooks for API Integration:**
```typescript
// src/hooks/useFeature.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Feature, FeatureCreate } from '../types/feature';

export const useFeature = () => {
  const queryClient = useQueryClient();

  const { data: features, isLoading } = useQuery({
    queryKey: ['features'],
    queryFn: () => api.get('/api/features').then(res => res.data),
  });

  const createFeature = useMutation({
    mutationFn: (data: FeatureCreate) => 
      api.post('/api/features', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['features'] });
    },
  });

  return { features, createFeature, isLoading };
};
```

### **Type Definitions (Mirror Backend):**
```typescript
// src/types/feature.ts
export interface Feature {
  id: string;
  user_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface FeatureCreate {
  title: string;
  description: string;
}

export interface FeatureUpdate {
  title?: string;
  description?: string;
}
```

## 🔐 **Authentication Integration**

### **JWT Token Management:**
```typescript
// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import api from '../services/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/api/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Get user profile
      const userResponse = await api.get('/api/users/me');
      setUser(userResponse.data);
      setIsAuthenticated(true);
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setIsAuthenticated(false);
  };

  return { user, isAuthenticated, login, logout };
};
```

### **Protected Route Component:**
```typescript
// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

## 🧪 **Frontend Testing Patterns**

### **Component Testing:**
```typescript
// src/components/FeatureName/FeatureName.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeatureName } from './FeatureName';

const queryClient = new QueryClient();

const renderWithQueryClient = (component: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('FeatureName', () => {
  it('renders feature form and list', () => {
    renderWithQueryClient(<FeatureName />);
    
    expect(screen.getByText('Create Feature')).toBeInTheDocument();
    expect(screen.getByText('Feature List')).toBeInTheDocument();
  });

  it('submits new feature', async () => {
    renderWithQueryClient(<FeatureName />);
    
    const titleInput = screen.getByLabelText('Title');
    const submitButton = screen.getByText('Create');
    
    fireEvent.change(titleInput, { target: { value: 'Test Feature' } });
    fireEvent.click(submitButton);
    
    // Test submission behavior
  });
});
```

### **API Integration Testing:**
```typescript
// src/hooks/useFeature.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useFeature } from './useFeature';
import api from '../services/api';

// Mock API calls
jest.mock('../services/api');

const queryClient = new QueryClient();

const renderHookWithQueryClient = () => {
  return renderHook(() => useFeature(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    ),
  });
};

describe('useFeature', () => {
  it('fetches features on mount', async () => {
    const mockFeatures = [{ id: '1', title: 'Test Feature' }];
    (api.get as jest.Mock).mockResolvedValue({ data: mockFeatures });

    const { result } = renderHookWithQueryClient();

    await waitFor(() => {
      expect(result.current.features).toEqual(mockFeatures);
    });
  });
});
```

## 💰 **Cost Optimization Strategies**

### **1. Extend Your .cursorrules:**
```json
{
  "description": "Frontend development optimizations",
  "settings": {
    "cache_frontend_patterns": true,
    "learn_component_structure": true,
    "understand_ui_patterns": true,
    "cache_styling_conventions": true,
    "smart_context_switching": true
  }
}
```

### **2. Frontend Quick Reference:**
Add to your `quick_reference.md`:
```markdown
## 🌐 Frontend Patterns

### Component Structure:
- Use functional components with hooks
- Follow naming: ComponentName.tsx
- Organize by feature, not type

### API Integration:
- Use custom hooks for API calls
- Handle loading/error states consistently
- Follow REST conventions from backend
```

### **3. Pattern Recognition:**
- **Backend questions** → Use cached backend knowledge (79,150 tokens)
- **Frontend questions** → Use cached frontend patterns
- **Integration questions** → Combine both efficiently

## 🚀 **Development Workflow**

### **1. Start with Backend (Efficient):**
```bash
# AI already knows your backend patterns
# Use cached knowledge for API development
# Token usage: ~692 (like your current efficiency)
```

### **2. Add Frontend (Learning Phase):**
```bash
# AI learns new frontend patterns
# Higher token usage initially (5,000-10,000)
# Establishes frontend conventions
```

### **3. Full-Stack Development (Optimal):**
```bash
# AI uses cached knowledge for both domains
# Efficient context switching
# Token usage: 1,000-5,000 (both domains cached)
```

## 📊 **Expected Token Usage Evolution**

### **Current (Backend Only):**
- **Efficiency**: 99.1% cache usage
- **Cost**: 75-80% reduction

### **With Frontend (Phase 1):**
- **Efficiency**: 70-80% cache usage
- **Cost**: 60-70% reduction

### **With Frontend (Phase 3):**
- **Efficiency**: 90-95% cache usage
- **Cost**: 80-85% total reduction

## 🎯 **Best Practices for AI Efficiency**

### **1. Ask Domain-Specific Questions:**
```
✅ "How do I create a React component for user management?"
✅ "How do I integrate the user API endpoint with React Query?"
❌ "How do I build a full-stack user management system?"
```

### **2. Reference Existing Patterns:**
```
✅ "Follow the same pattern as the FeatureName component"
✅ "Use the same API integration approach as the auth hook"
❌ "Create a completely new approach"
```

### **3. Batch Related Questions:**
```
✅ "Help me set up the user management feature: component, hook, and API integration"
❌ "How do I create a user component?" (then separately) "How do I create a user hook?"
```

## 🔄 **Integration with Existing Tutorials**

### **Use Your Enhanced AI System:**
1. **Backend features** → Follow `building-a-feature.md` (6-step pattern)
2. **Frontend components** → Follow this guide's patterns
3. **Full-stack features** → Combine both approaches
4. **AI assistance** → Leverage cached knowledge from both domains

### **Reference Files:**
- **`building-a-feature.md`** - Backend development patterns
- **`quick_reference.md`** - Common patterns and conventions
- **`agent_setup.md`** - Environment setup for AI agents
- **`frontend_ai_development.md`** - Frontend development patterns

## 🎉 **The Result:**

Your AI system will evolve from:
- **"Backend expert"** (current state)
- **"Full-stack expert"** (with frontend development)

**Maintaining efficiency while expanding capabilities!** 🚀

---

**Ready to build full-stack applications with AI-optimized development?** 🌐✨

Your enhanced `.cursorrules` will scale with your project, providing efficient AI assistance across the entire development stack!
