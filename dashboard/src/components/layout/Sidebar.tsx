"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    ScanLine,
    LineChart,
    BookOpen,
    Settings,
    Activity,
    Zap,
    Wallet,
    BarChart3,
    Shield,
    TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSystemData } from "@/hooks/useSystemData";

const navigation = [
    { name: "Command Center", href: "/", icon: LayoutDashboard },
    { name: "Signal Engine", href: "/signals", icon: BarChart3 },
    { name: "Risk Manager", href: "/risk", icon: Shield },
    { name: "Account & Stats", href: "/account", icon: Wallet },
    { name: "Live Scanner", href: "/scanner", icon: ScanLine },
    { name: "Options", href: "/options", icon: TrendingUp },
    { name: "Active Positions", href: "/positions", icon: LineChart },
    { name: "Journal & Stats", href: "/journal", icon: BookOpen },
    { name: "System Config", href: "/settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const { isConnected } = useSystemData();

    return (
        <div className="flex h-screen w-64 flex-col fixed left-0 top-0 border-r border-glass-border bg-glass backdrop-blur-xl z-50">
            {/* Logo Area */}
            <div className="flex h-16 items-center gap-2 px-6 border-b border-glass-border">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
                    <Zap className="h-5 w-5 fill-current" />
                </div>
                <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                    NEURO TRADER
                </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 px-3 py-4">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-primary/10 text-primary shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                            )}
                        >
                            <item.icon
                                className={cn(
                                    "h-5 w-5 flex-shrink-0 transition-colors",
                                    isActive ? "text-primary" : "text-gray-500 group-hover:text-gray-300"
                                )}
                            />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            {/* System Status Footer */}
            <div className="border-t border-glass-border p-4">
                <div className="rounded-lg bg-black/20 p-3">
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Activity className={cn("h-3 w-3", isConnected ? "text-success animate-pulse" : "text-accent")} />
                        <span>{isConnected ? "System Online" : "Disconnected"}</span>
                    </div>
                    <div className="mt-2 text-[10px] text-gray-500 font-mono">
                        v4.0 Live
                    </div>
                </div>
            </div>
        </div>
    );
}
