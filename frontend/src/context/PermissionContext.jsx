import React, { createContext, useContext, useState, useEffect } from 'react';

const PermissionContext = createContext();

export const PermissionProvider = ({ children, API_BASE }) => {
    const [permissions, setPermissions] = useState({});
    const [role, setRole] = useState(null);
    const [loading, setLoading] = useState(true);

    const refreshPermissions = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/auth/permissions`, { credentials: 'include' });
            if (res.ok) {
                const data = await res.json();
                setPermissions(data.permissions || {});
                setRole(data.role);
            }
        } catch (err) {
            console.error("Failed to fetch permissions", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshPermissions();
    }, []);

    const hasPermission = (module, action = 'access') => {
        if (!permissions[module]) return false;
        return permissions[module].includes(action);
    };

    return (
        <PermissionContext.Provider value={{ permissions, role, loading, hasPermission, refreshPermissions }}>
            {children}
        </PermissionContext.Provider>
    );
};

export const usePermissions = () => {
    const context = useContext(PermissionContext);
    if (!context) {
        throw new Error("usePermissions must be used within a PermissionProvider");
    }
    return context;
};
