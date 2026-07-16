import { Link, Outlet } from "react-router-dom";
import { Link2, LogOut, User as UserIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/dashboard" className="flex items-center gap-2 font-semibold">
            <Link2 className="h-5 w-5" />
            Snip
          </Link>

          <div className="flex items-center gap-1">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="ghost" className="gap-2 px-1.5" />}>
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="text-xs">
                    {user?.username?.slice(0, 2).toUpperCase() ?? <UserIcon className="h-3 w-3" />}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm">{user?.username}</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onClick={logout}>
                  <LogOut />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
