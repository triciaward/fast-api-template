# 🌐 Cross-Platform AI Development with Enhanced .cursorrules

**Leverage your optimized AI system for efficient web AND mobile development!**

This guide shows how to extend your AI-optimized FastAPI template to include cross-platform frontend development while maintaining the same efficiency and quality standards.

## 🎯 **What You'll Learn**

- **How AI adapts** to cross-platform development
- **Maintaining efficiency** across web, mobile, and backend
- **Framework-specific patterns** and conventions
- **Integration strategies** between platforms and backend
- **Cost optimization** for multi-platform development

## 🚀 **How Your Enhanced .cursorrules Handle Frontend**

### **Current Backend Efficiency:**
- **Cache usage**: 99.1% (79,150 tokens from cache)
- **Cost reduction**: 75-80% compared to default
- **Project knowledge**: AI understands your 173 test files and patterns

### **Cross-Platform Development Evolution:**
- **Phase 1**: Learning new patterns (higher token usage)
- **Phase 2**: Established conventions (lower token usage)
- **Phase 3**: Multi-platform efficiency (optimal token usage)

## 📁 **Cross-Platform Project Structure**

### **Recommended Organization:**
```
fast-api-template/
├── app/                        # Backend (cached, efficient)
├── web/                        # Web application (React/Vue/Angular)
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
├── mobile/                     # Mobile application (React Native/Flutter)
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── screens/           # Screen-level components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API integration services
│   │   ├── utils/             # Mobile utilities
│   │   ├── styles/            # Mobile-specific styles
│   │   └── types/             # TypeScript type definitions
│   ├── android/               # Android-specific files
│   ├── ios/                   # iOS-specific files
│   ├── package.json           # Dependencies and scripts
│   └── app.json               # App configuration
├── shared/                     # Shared code between platforms
│   ├── types/                 # Common TypeScript types
│   ├── services/              # Shared API services
│   ├── utils/                 # Common utilities
│   └── constants/             # Shared constants
├── docs/tutorials/            # Backend guides (cached)
├── docs/frontend/             # Cross-platform guides
└── .cursorrules               # AI optimization rules
```

### **Integration Points:**
- **API endpoints** - Connect to your FastAPI backend
- **Authentication** - Use JWT tokens from backend
- **Data models** - Mirror backend schemas in TypeScript
- **Error handling** - Consistent patterns across stack
- **Shared services** - Common API integration code
- **Type definitions** - Unified data models across platforms

## 🎯 **Framework Selection Guide**

### **Web Frameworks:**
- **React** - Most popular, extensive ecosystem, TypeScript support
- **Vue.js** - Progressive framework, easy learning curve, composition API
- **Angular** - Enterprise-grade, full-featured, strong typing
- **Svelte** - Compile-time framework, excellent performance, modern syntax

### **Mobile Frameworks:**
- **React Native** - JavaScript/TypeScript, native performance, cross-platform
- **Flutter** - Dart language, single codebase, excellent performance
- **Ionic** - Web technologies, hybrid apps, capacitor support
- **Xamarin** - C# language, .NET ecosystem, native performance

### **Cross-Platform Strategies:**
- **Shared Backend** - Single FastAPI backend serving all platforms
- **Shared Types** - Common TypeScript interfaces across platforms
- **Shared Services** - Unified API integration code
- **Platform-Specific UI** - Native components for each platform

## 🔧 **Setting Up Cross-Platform Development**

### **1. Initialize Web Application:**
```bash
# Create web directory
mkdir web
cd web

# React with TypeScript
npx create-react-app . --template typescript

# Or use Vite for faster development
npm create vite@latest . -- --template react-ts

# Vue.js with TypeScript
npm create vue@latest . -- --typescript

# Angular with TypeScript
npx @angular/cli@latest new . --routing --style=scss
```

### **2. Initialize Mobile Application:**
```bash
# Create mobile directory
mkdir mobile
cd mobile

# React Native with TypeScript
npx react-native@latest init MyApp --template react-native-template-typescript

# Flutter with Dart
flutter create . --org com.yourcompany --project-name my_app

# Ionic with React
npm init @ionic/app@latest . --type=react --capacitor

# Xamarin (requires Visual Studio)
# Use Visual Studio templates for Xamarin.Forms
```

### **3. Install Web Dependencies:**
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

### **4. Install Mobile Dependencies:**
```bash
# React Native
npm install @react-navigation/native @react-navigation/stack
npm install react-native-vector-icons react-native-gesture-handler
npm install @react-native-async-storage/async-storage

# Flutter (add to pubspec.yaml)
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  provider: ^6.1.1
  shared_preferences: ^2.2.2

# Ionic
npm install @ionic/react @ionic/react-router
npm install @capacitor/core @capacitor/cli
```

### **5. Install Shared Dependencies:**
```bash
# In shared directory
npm install axios zod date-fns
npm install --save-dev typescript @types/node
```

### **6. Configure Shared API Integration:**
```typescript
// shared/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Platform-agnostic token storage
const getToken = () => {
  if (typeof window !== 'undefined') {
    // Web platform
    return localStorage.getItem('access_token');
  } else {
    // Mobile platform
    // Use AsyncStorage for React Native, SharedPreferences for Flutter
    return null; // Will be implemented per platform
  }
};

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### **7. Platform-Specific API Configuration:**
```typescript
// web/src/services/api.ts
import api from '../../../shared/services/api';

// Web-specific configuration
const webApi = api.create({
  // Web-specific settings
});

export default webApi;
```

```typescript
// mobile/src/services/api.ts
import api from '../../../shared/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mobile-specific configuration
const mobileApi = api.create({
  // Mobile-specific settings
});

// Override token storage for mobile
mobileApi.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default mobileApi;
```

## 🎨 **Cross-Platform Development Patterns**

### **Shared Type Definitions:**
```typescript
// shared/types/feature.ts
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

### **Web Component Structure (React):**
```typescript
// web/src/components/FeatureName/FeatureName.tsx
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

### **Mobile Component Structure (React Native):**
```typescript
// mobile/src/components/FeatureName/FeatureName.tsx
import React from 'react';
import { View, Text, ScrollView } from 'react-native';
import { useFeature } from './useFeature';
import { FeatureForm } from './FeatureForm';
import { FeatureList } from './FeatureList';

interface FeatureNameProps {
  // Props interface
}

export const FeatureName: React.FC<FeatureNameProps> = (props) => {
  const { features, createFeature, isLoading } = useFeature();

  return (
    <ScrollView style={styles.container}>
      <FeatureForm onSubmit={createFeature} />
      <FeatureList features={features} isLoading={isLoading} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
});
```

### **Mobile Component Structure (Flutter):**
```dart
// mobile/lib/components/feature_name.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/feature_provider.dart';

class FeatureName extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<FeatureProvider>(
      builder: (context, featureProvider, child) {
        return Scaffold(
          body: Column(
            children: [
              FeatureForm(),
              FeatureList(),
            ],
          ),
        );
      },
    );
  }
}
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

## 🧪 **Cross-Platform Testing Patterns**

### **Web Component Testing (React):**
```typescript
// web/src/components/FeatureName/FeatureName.test.tsx
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

### **Mobile Component Testing (React Native):**
```typescript
// mobile/src/components/FeatureName/FeatureName.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { FeatureName } from './FeatureName';

describe('FeatureName', () => {
  it('renders feature form and list', () => {
    const { getByText } = render(<FeatureName />);
    
    expect(getByText('Create Feature')).toBeTruthy();
    expect(getByText('Feature List')).toBeTruthy();
  });

  it('submits new feature', async () => {
    const { getByText, getByPlaceholderText } = render(<FeatureName />);
    
    const titleInput = getByPlaceholderText('Enter title');
    const submitButton = getByText('Create');
    
    fireEvent.changeText(titleInput, 'Test Feature');
    fireEvent.press(submitButton);
    
    // Test submission behavior
  });
});
```

### **Mobile Component Testing (Flutter):**
```dart
// mobile/test/components/feature_name_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/components/feature_name.dart';

void main() {
  group('FeatureName', () {
    testWidgets('renders feature form and list', (WidgetTester tester) async {
      await tester.pumpWidget(FeatureName());
      
      expect(find.text('Create Feature'), findsOneWidget);
      expect(find.text('Feature List'), findsOneWidget);
    });

    testWidgets('submits new feature', (WidgetTester tester) async {
      await tester.pumpWidget(FeatureName());
      
      final titleField = find.byType(TextField);
      final submitButton = find.text('Create');
      
      await tester.enterText(titleField, 'Test Feature');
      await tester.tap(submitButton);
      
      // Test submission behavior
    });
  });
}
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

## 💰 **Cross-Platform Cost Optimization Strategies**

### **1. Extend Your .cursorrules:**
```json
{
  "description": "Cross-platform development optimizations",
  "settings": {
    "cache_web_patterns": true,
    "cache_mobile_patterns": true,
    "learn_framework_specific_patterns": true,
    "understand_cross_platform_conventions": true,
    "cache_shared_code_patterns": true,
    "smart_platform_context_switching": true
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

## 🚀 **Cross-Platform Development Workflow**

### **1. Start with Backend (Efficient):**
```bash
# AI already knows your backend patterns
# Use cached knowledge for API development
# Token usage: ~692 (like your current efficiency)
```

### **2. Add Web Development (Learning Phase):**
```bash
# AI learns web framework patterns (React/Vue/Angular)
# Higher token usage initially (5,000-10,000)
# Establishes web development conventions
```

### **3. Add Mobile Development (Learning Phase):**
```bash
# AI learns mobile framework patterns (React Native/Flutter)
# Higher token usage initially (5,000-10,000)
# Establishes mobile development conventions
```

### **4. Cross-Platform Development (Optimal):**
```bash
# AI uses cached knowledge for all domains
# Efficient context switching between platforms
# Token usage: 1,000-5,000 (all domains cached)
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
- **"Web development expert"** (with web frameworks)
- **"Mobile development expert"** (with mobile frameworks)
- **"Cross-platform expert"** (with all platforms)

**Maintaining efficiency while expanding capabilities across platforms!** 🚀

---

**Ready to build cross-platform applications with AI-optimized development?** 🌐📱✨

Your enhanced `.cursorrules` will scale with your project, providing efficient AI assistance across web, mobile, and backend development!
