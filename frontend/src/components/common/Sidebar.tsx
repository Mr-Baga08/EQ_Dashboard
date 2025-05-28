// frontend/src/components/common/Sidebar.tsx
import React from 'react';
import { useRouter } from 'next/router';
import { 
  HomeIcon, 
  UsersIcon, 
  ChartBarIcon,
  ArrowRightOnRectangleIcon 
} from '@heroicons/react/24/outline';

const Sidebar: React.FC = () => {
  const router = useRouter();

  const menuItems = [
    { icon: HomeIcon, label: 'Dashboard', path: '/' },
    { icon: UsersIcon, label: 'Clients', path: '/clients' },
    { icon: ChartBarIcon, label: 'Analytics', path: '/analytics' },
    { icon: ArrowRightOnRectangleIcon, label: 'Exit Positions', path: '/exit' },
  ];

  return (
    <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
      <div className="p-6">
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.path;
            
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;