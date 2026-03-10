import * as React from "react"

const Tabs = ({ defaultValue, children, className }) => {
    const [activeTab, setActiveTab] = React.useState(defaultValue)
    return (
        <div className={className}>
            {React.Children.map(children, child => {
                if (child.type === TabsList || child.type === TabsContent) {
                    return React.cloneElement(child, { activeTab, setActiveTab })
                }
                return child
            })}
        </div>
    )
}

const TabsList = ({ children, className, activeTab, setActiveTab }) => (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground ${className}`}>
        {React.Children.map(children, child => React.cloneElement(child, { activeTab, setActiveTab }))}
    </div>
)

const TabsTrigger = ({ value, children, activeTab, setActiveTab, className }) => (
    <button
        onClick={() => setActiveTab(value)}
        className={`inline-flex items-center justify-center控制 whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${activeTab === value ? "bg-background text-foreground shadow-sm" : ""} ${className}`}
    >
        {children}
    </button>
)

const TabsContent = ({ value, children, activeTab, className }) => (
    activeTab === value ? <div className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${className}`}>{children}</div> : null
)

export { Tabs, TabsList, TabsTrigger, TabsContent }
