import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dna, TrendingUp, Database, Zap, ArrowRight, X, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';

// ==============================
// COMPONENTE: NoiseOverlay
// ==============================
function NoiseOverlay() {
  return (
    <div className="fixed inset-0 pointer-events-none z-50 opacity-[0.015]">
      <svg className="w-full h-full">
        <filter id="noiseFilter">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noiseFilter)" />
      </svg>
    </div>
  );
}

// ==============================
// COMPONENTE: ShaderBackground
// ==============================
function ShaderBackground() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const particlesRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationId;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Criar partículas
    const particleCount = 80;
    particlesRef.current = Array.from({ length: particleCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 1,
    }));

    const handleMouseMove = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);

    function draw() {
      ctx.fillStyle = 'rgba(253, 251, 249, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((p, i) => {
        // Interação com mouse
        const dx = mouseRef.current.x - p.x;
        const dy = mouseRef.current.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          const force = (150 - dist) / 150;
          p.vx -= (dx / dist) * force * 0.2;
          p.vy -= (dy / dist) * force * 0.2;
        }

        p.x += p.vx;
        p.y += p.vy;

        // Fricção
        p.vx *= 0.98;
        p.vy *= 0.98;

        // Bordas
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        // Desenhar partícula
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(34, 197, 94, 0.4)';
        ctx.fill();

        // Linhas entre partículas próximas
        particlesRef.current.slice(i + 1).forEach((p2) => {
          const dx2 = p.x - p2.x;
          const dy2 = p.y - p2.y;
          const dist2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
          if (dist2 < 100) {
            ctx.strokeStyle = `rgba(34, 197, 94, ${0.15 * (1 - dist2 / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        });
      });

      animationId = requestAnimationFrame(draw);
    }
    draw();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0" />;
}

// ==============================
// COMPONENTE: LoginPage
// ==============================
function LoginPage({ onBack }) {
  const [activeTab, setActiveTab] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const endpoint = activeTab === 'login' ? '/api/auth/login' : '/api/auth/register';
      const payload = activeTab === 'login'
        ? { email: formData.email, password: formData.password }
        : { name: formData.name, email: formData.email, password: formData.password };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        // Redirect to dashboard on success
        window.location.href = '/dashboard';
      } else {
        alert(data.error || 'Erro ao processar requisição');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao conectar com o servidor');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[9999] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4"
    >
      {/* Background particles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(30)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-green-400 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -30, 0],
              opacity: [0.2, 0.5, 0.2],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      {/* Login Card */}
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="relative w-full max-w-md"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl blur-xl opacity-20" />

        <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden">
          {/* Close button */}
          <button
            onClick={onBack}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors z-10"
          >
            <X size={24} />
          </button>

          {/* Header */}
          <div className="p-8 pb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <Dna className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white">Genefy</h2>
            </div>
            <p className="text-slate-400 text-sm">Sistema de Acasalamento Genético</p>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-700/50 px-8">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
                activeTab === 'login' ? 'text-green-400' : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Entrar
              {activeTab === 'login' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-500"
                />
              )}
            </button>
            <button
              onClick={() => setActiveTab('register')}
              className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
                activeTab === 'register' ? 'text-green-400' : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              Criar Conta
              {activeTab === 'register' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-500"
                />
              )}
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            <AnimatePresence mode="wait">
              {activeTab === 'register' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Nome Completo
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full bg-slate-900/50 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-green-500 transition-colors"
                        placeholder="Seu nome"
                        required={activeTab === 'register'}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="seu@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg pl-10 pr-12 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium py-2.5 rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {activeTab === 'login' ? 'Entrar' : 'Criar Conta'}
            </button>
          </form>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ==============================
// COMPONENTE: Navbar
// ==============================
function Navbar({ onLoginClick }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/80 backdrop-blur-md shadow-lg' : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <Dna className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              Genefy
            </span>
          </div>
          <button
            onClick={onLoginClick}
            className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium rounded-full hover:shadow-lg hover:scale-105 transition-all"
          >
            Acessar Sistema
          </button>
        </div>
      </div>
    </motion.nav>
  );
}

// ==============================
// COMPONENTE: Hero
// ==============================
function Hero({ onCtaClick }) {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      <ShaderBackground />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-block mb-6 px-4 py-2 bg-green-50 border border-green-200 rounded-full"
          >
            <span className="text-green-700 text-sm font-medium">
              🧬 Tecnologia de Ponta em Genética
            </span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-bold text-slate-900 mb-6 leading-tight">
            Otimização Genética
            <br />
            <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              Baseada em Algoritmos
            </span>
          </h1>

          <p className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
            Sistema avançado de acasalamento para gado leiteiro utilizando algoritmos genéticos e
            análise de consanguinidade em tempo real.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onCtaClick}
              className="px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 group"
            >
              Começar Agora
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>
          </div>
        </motion.div>

        {/* Floating Cards */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {[
            { icon: Dna, title: 'Algoritmos Genéticos', desc: 'Otimização inteligente' },
            { icon: TrendingUp, title: 'Ganho Genético', desc: 'Resultados mensuráveis' },
            { icon: Database, title: 'Big Data', desc: 'Análise em tempo real' },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-green-100 hover:border-green-300 transition-all hover:-translate-y-2"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center mb-4">
                <item.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">{item.title}</h3>
              <p className="text-slate-600 text-sm">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ==============================
// COMPONENTE: BentoGrid
// ==============================
function BentoGrid() {
  const features = [
    {
      title: 'Algoritmo Genético',
      desc: 'Seleção natural aplicada ao melhoramento genético',
      gradient: 'from-green-400 to-emerald-500',
      size: 'md:col-span-2',
    },
    {
      title: 'Análise de Consanguinidade',
      desc: 'Prevenção automática de endogamia',
      gradient: 'from-emerald-400 to-teal-500',
      size: 'md:col-span-1',
    },
    {
      title: 'Dashboard em Tempo Real',
      desc: 'Visualize métricas e ganhos genéticos',
      gradient: 'from-teal-400 to-cyan-500',
      size: 'md:col-span-1',
    },
    {
      title: 'Importação Automática',
      desc: 'Excel e PDF processados automaticamente',
      gradient: 'from-cyan-400 to-blue-500',
      size: 'md:col-span-2',
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-slate-50 to-white relative">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Recursos Avançados
          </h2>
          <p className="text-xl text-slate-600">
            Tecnologia de ponta para o melhoramento genético
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className={`${feature.size} group relative overflow-hidden rounded-3xl bg-gradient-to-br ${feature.gradient} p-8 text-white hover:scale-[1.02] transition-transform cursor-pointer`}
            >
              <div className="relative z-10">
                <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
                <p className="text-white/90">{feature.desc}</p>
              </div>
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ==============================
// COMPONENTE: TechnicalSpecs
// ==============================
function TechnicalSpecs() {
  const specs = [
    { label: 'Backend', value: 'Python + Flask' },
    { label: 'Frontend', value: 'React + Tailwind' },
    { label: 'Banco de Dados', value: 'SQLite' },
    { label: 'Algoritmo', value: 'Genético + IA' },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <Zap className="w-16 h-16 mx-auto mb-6 text-green-400" />
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Stack Técnico</h2>
          <p className="text-xl text-slate-400">
            Desenvolvido com as melhores tecnologias
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {specs.map((spec, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="bg-slate-800 rounded-2xl p-6 border border-slate-700 hover:border-green-500 transition-colors"
            >
              <div className="text-green-400 text-sm font-semibold mb-2">{spec.label}</div>
              <div className="text-white text-lg font-bold">{spec.value}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ==============================
// COMPONENTE: Footer
// ==============================
function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
            <Dna className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">Genefy</span>
        </div>
        <p className="text-sm">
          Sistema de Acasalamento Genético para Gado Leiteiro &copy; 2025
        </p>
      </div>
    </footer>
  );
}

// ==============================
// COMPONENTE PRINCIPAL
// ==============================
export default function GenefyLanding() {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <div className="bg-[#FDFBF9] min-h-screen font-sans text-slate-900">
      <NoiseOverlay />
      <Navbar onLoginClick={() => setShowLogin(true)} />
      <Hero onCtaClick={() => setShowLogin(true)} />
      <BentoGrid />
      <TechnicalSpecs />
      <Footer />
      <AnimatePresence>
        {showLogin && <LoginPage onBack={() => setShowLogin(false)} />}
      </AnimatePresence>
    </div>
  );
}
