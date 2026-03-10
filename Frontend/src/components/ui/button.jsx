import * as React from "react"

const Button = React.forwardRef(({ className, variant, ...props }, ref) => {
    const variants = {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
    }
    const cls = variants[variant] || variants.default

    return (
        <button
            className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2 ${cls} ${className}`}
            ref={ref}
            {...props}
        />
    )
})
Button.displayName = "Button"

export { Button }
