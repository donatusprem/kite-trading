"use client";

import { Bell, Search, User } from "lucide-react";
import { useAccountData } from "@/hooks/useSystemData";

export function Header() {
    const { account } = useAccountData();

    const userName = account?.user_name || "Trader";
    const userShortname = account?.user_shortname || "";
    const broker = account?.broker || "";

    return (
        <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-glass-border bg-glass backdrop-blur-md px-6 ml-64">
            {/* Search / Breadcrumbs */}
            <div className="flex items-center gap-4">
                <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search symbol..."
                        className="h-9 w-64 rounded-full border border-glass-border bg-black/20 pl-9 text-sm text-gray-300 placeholder:text-gray-600 focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/50"
                    />
                </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
                <button className="relative rounded-full p-2 text-gray-400 hover:bg-white/5 hover:text-white transition-colors">
                    <Bell className="h-5 w-5" />
                    <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-accent animate-pulse-slow"></span>
                </button>

                <div className="h-8 w-px bg-glass-border mx-1"></div>

                <div className="flex items-center gap-3 pl-1">
                    <div className="text-right hidden md:block">
                        <div className="text-sm font-medium text-white">{userName}</div>
                        <div className="text-xs text-gray-500">{broker} Account</div>
                    </div>
                    <div className="h-9 w-9 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-glass-border flex items-center justify-center">
                        {userShortname ? (
                            <span className="text-xs font-bold text-gray-300">{userShortname.charAt(0)}</span>
                        ) : (
                            <User className="h-5 w-5 text-gray-400" />
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
