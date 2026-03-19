import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, useScroll } from 'framer-motion';
import { Activity, Menu, X, ChevronRight } from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';

export function Header({ branding }) {
    const [isScrolled, setIsScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { scrollY } = useScroll();
    const navigate = useNavigate();

    useEffect(() => {
        return scrollY.onChange((latest) => {
            setIsScrolled(latest > 10);
        });
    }, [scrollY]);

    const navLinks = [
        { to: '/dashboard', label: 'Dashboard' },
        { to: '/features', label: 'Features' },
        { to: '/pricing', label: 'Pricing' },
        { to: '/docs', label: 'Docs' },
    ];

    return (
        <motion.header
            className={cn(
                "fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b",
                isScrolled
                    ? "bg-white/80 backdrop-blur-md border-slate-200/50 shadow-sm py-3"
                    : "bg-transparent border-transparent py-5"
            )}
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                {/* Logo */}
                <NavLink
                    to="/"
                    className="flex items-center gap-2 cursor-pointer group"
                >
                    {branding?.logoUrl ? (
                        <img src={branding.logoUrl} alt="Company Logo" className="h-10 w-auto object-contain transition-transform group-hover:scale-105" />
                    ) : (
                        <>
                            <div className="bg-brand-600 text-white p-2 rounded-xl shadow-lg shadow-brand-500/20 transition-transform group-hover:scale-105 group-hover:rotate-3">
                                <Activity size={24} strokeWidth={2.5} />
                            </div>
                            <span className="font-bold text-xl tracking-tight text-slate-900 group-hover:text-brand-600 transition-colors">
                                SEO Health
                            </span>
                        </>
                    )}
                </NavLink>

                {/* Desktop Nav */}
                <nav className="hidden md:flex items-center gap-1 bg-slate-100/50 p-1 rounded-full border border-slate-200/50 backdrop-blur-sm">
                    {navLinks.map((link) => (
                        <NavLink
                            key={link.to}
                            to={link.to}
                            className={({ isActive }) =>
                                cn(
                                    "px-4 py-2 text-sm font-medium rounded-full transition-all duration-200",
                                    isActive
                                        ? "bg-white text-brand-600 shadow-sm"
                                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
                                )
                            }
                        >
                            {link.label}
                        </NavLink>
                    ))}
                </nav>

                {/* Actions */}
                <div className="hidden md:flex items-center gap-3">
                    <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                        Sign In
                    </Button>
                    <Button
                        variant="premium"
                        size="sm"
                        className="rounded-full px-6"
                        onClick={() => navigate('/')}
                    >
                        Get Audit <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                </div>

                {/* Mobile Menu Toggle */}
                <button
                    className="md:hidden p-2 text-slate-600 hover:text-brand-600"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                    {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="md:hidden bg-white border-b border-slate-100"
                >
                    <div className="px-4 py-6 space-y-4">
                        {navLinks.map((link) => (
                            <NavLink
                                key={link.to}
                                to={link.to}
                                onClick={() => setMobileMenuOpen(false)}
                                className={({ isActive }) =>
                                    cn(
                                        "block w-full text-left px-4 py-3 text-base font-medium rounded-lg",
                                        isActive
                                            ? "bg-brand-50 text-brand-600"
                                            : "text-slate-600 hover:bg-slate-50 hover:text-brand-600"
                                    )
                                }
                            >
                                {link.label}
                            </NavLink>
                        ))}
                        <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
                            <Button variant="outline" className="w-full justify-center" onClick={() => navigate('/login')}>Sign In</Button>
                            <Button variant="premium" className="w-full justify-center" onClick={() => navigate('/')}>Get Free Audit</Button>
                        </div>
                    </div>
                </motion.div>
            )}
        </motion.header>
    );
}
