import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import { Dna, ShieldCheck, ArrowRight, CheckCircle2, Menu, Microscope, Activity, Lock, Mail, Eye, EyeOff } from 'lucide-react';

// --- Utils & Assets ---

const NoiseOverlay = () => (
  <div className="fixed inset-0 w-full h-full pointer-events-none z-50 opacity-[0.03] mix-blend-overlay"
    style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}
  />
);

// --- Shader Animation Component ---

const ShaderBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    let animationFrameId;
    let mouse = { x: -1000, y: -1000 }; // Start mouse off-screen

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
      initParticles();
    };

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.size = Math.random() * 2 + 0.5;
        this.baseX = this.x;
        this.baseY = this.y;
        this.density = (Math.random() * 30) + 1;
      }

      update() {
        let dx = mouse.x - this.x;
        let dy = mouse.y - this.y;
        let distance = Math.sqrt(dx * dx + dy * dy);
        let maxDistance = 200;
        let forceDirectionX = dx / distance;
        let forceDirectionY = dy / distance;
        let force = (maxDistance - distance) / maxDistance;

        if (distance < maxDistance) {
          this.x -= forceDirectionX * force * this.density;
          this.y -= forceDirectionY * force * this.density;
        } else {
          if (this.x !== this.baseX) {
            let dx = this.x - this.baseX;
            this.x -= dx / 20;
          }
          if (this.y !== this.baseY) {
            let dy = this.y - this.baseY;
            this.y -= dy / 20;
          }
        }
      }

      draw() {
        ctx.fillStyle = 'rgba(139, 92, 246, 0.8)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fill();
      }
    }

    const initParticles = () => {
      particles = [];
      let numberOfParticles = (width * height) / 15000; // Density
      for (let i = 0; i < numberOfParticles; i++) {
        particles.push(new Particle());
      }
    };

    const connect = () => {
      for (let a = 0; a < particles.length; a++) {
        for (let b = a; b < particles.length; b++) {
          let dx = particles[a].x - particles[b].x;
          let dy = particles[a].y - particles[b].y;
          let distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 120) {
            let opacityValue = 1 - (distance / 120);
            ctx.strokeStyle = `rgba(139, 92, 246, ${opacityValue * 0.5})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(particles[a].x, particles[a].y);
            ctx.lineTo(particles[b].x, particles[b].y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
      }
      connect();
      animationFrameId = requestAnimationFrame(animate);
    };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', handleMouseMove);

    resize();
    animate();

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full z-0 pointer-events-none" />;
};

// --- Login Component (Immersive Dark Mode) ---

const LoginPage = ({ onBack }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const payload = isLogin
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
        setError(data.error || 'Erro ao processar requisição');
      }
    } catch (err) {
      console.error('Erro:', err);
      setError('Erro ao conectar com o servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed inset-0 z-50 bg-slate-900 flex items-center justify-center p-4 overflow-hidden font-sans"
    >
      {/* Immersive Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-indigo-950/40 to-slate-950 z-0"></div>
      <ShaderBackground />

      {/* Login Card */}
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ delay: 0.2, type: "spring", stiffness: 100 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="bg-slate-900/50 backdrop-blur-2xl rounded-none border border-white/10 shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 mb-6 rounded-sm shadow-lg shadow-indigo-500/20">
              <img src="https://img.icons8.com/ios-filled/50/ffffff/cow.png" alt="Logo" className="w-6 h-6" />
            </div>
            <h1 className="text-3xl font-serif text-white mb-2 tracking-tight">
              {isLogin ? 'Bem-vindo de volta' : 'Criar Nova Conta'}
            </h1>
            <p className="text-indigo-200/60 text-sm font-mono uppercase tracking-wider">
              {isLogin ? ':: GERENCIE SEU REBANHO ::' : ':: REVOLUCIONE SEU REBANHO ::'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Campo Nome - Apenas no Cadastro */}
            <AnimatePresence>
              {!isLogin && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="group overflow-hidden"
                >
                  <label className="block text-xs font-mono text-indigo-300 mb-2 uppercase tracking-wider">Nome da Propriedade / Proprietário</label>
                  <input
                    type="text"
                    className="w-full bg-white/5 border border-white/10 rounded-sm px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/10 transition-all font-sans"
                    placeholder="Ex: Fazenda Cavalli"
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="group">
              <label className="block text-xs font-mono text-indigo-300 mb-2 uppercase tracking-wider">Email Corporativo</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 group-focus-within:text-indigo-400 transition-colors" />
                <input
                  type="email"
                  className="w-full bg-white/5 border border-white/10 rounded-sm pl-12 pr-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/10 transition-all font-sans"
                  placeholder="nome@fazenda.com"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            <div className="group">
              <label className="block text-xs font-mono text-indigo-300 mb-2 uppercase tracking-wider">Senha</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 group-focus-within:text-indigo-400 transition-colors" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="w-full bg-white/5 border border-white/10 rounded-sm pl-12 pr-12 py-3 text-white placeholder-white/20 focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/10 transition-all font-sans"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors">
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white font-medium tracking-wide rounded-sm shadow-lg shadow-indigo-900/50 transition-all flex items-center justify-center gap-2 group"
            >
              <span>{loading ? 'Processando...' : (isLogin ? 'Acessar Sistema' : 'Começar Agora')}</span>
              {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 flex flex-col items-center gap-4 text-sm text-slate-400">
            <button onClick={() => setIsLogin(!isLogin)} className="hover:text-white transition-colors">
              {isLogin ? 'Novo por aqui? Crie sua conta' : 'Já é cliente? Fazer login'}
            </button>
            <button onClick={onBack} className="text-xs font-mono text-slate-600 hover:text-indigo-400 transition-colors mt-4 flex items-center gap-2">
              ← RETORNAR AO SITE
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// --- Landing Page Components (Light Mode) ---

const Navbar = ({ onLoginClick }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 w-full z-40 transition-all duration-500 border-b ${isScrolled ? 'bg-white/90 backdrop-blur-md border-slate-200 py-3' : 'bg-transparent border-transparent py-6'}`}>
      <div className="max-w-[1400px] mx-auto px-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-700 rounded-none flex items-center justify-center shadow-sm">
            <img src="https://img.icons8.com/ios-filled/50/ffffff/cow.png" alt="Logo" className="w-5 h-5" />
          </div>
          <span className="text-2xl font-serif tracking-tight text-slate-900">
            Genefy<span className="text-indigo-600">.</span>
          </span>
        </div>

        <div className="hidden md:flex items-center gap-12">
          {['Acasalamento', 'Genética', 'Sobre', 'Planos'].map((item) => (
            <a key={item} href={`#${item.toLowerCase()}`} className="text-sm uppercase tracking-widest text-slate-500 hover:text-indigo-700 font-medium transition-colors">
              {item}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-6">
          <button onClick={onLoginClick} className="text-slate-900 font-medium hover:text-indigo-700 transition-colors">Log in</button>
          <button onClick={onLoginClick} className="px-6 py-2.5 bg-slate-900 text-white text-sm tracking-wide hover:bg-indigo-700 transition-colors rounded-sm shadow-lg shadow-slate-900/10">
            Começar Agora
          </button>
        </div>

        <div className="md:hidden">
          <Menu className="text-slate-900" />
        </div>
      </div>
    </nav>
  );
};

const Hero = ({ onCtaClick }) => {
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 500], [0, 100]);
  const y2 = useTransform(scrollY, [0, 500], [0, -50]);

  return (
    <section className="relative pt-40 pb-20 lg:pt-52 lg:pb-32 overflow-hidden min-h-[90vh] flex items-center border-b border-slate-200 bg-[#FDFBF9]">
      <div className="absolute inset-0 w-full h-full pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(to right, #E2E8F0 1px, transparent 1px), linear-gradient(to bottom, #E2E8F0 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          opacity: 0.4
        }}>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        <div className="lg:col-span-7 flex flex-col gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-3 mb-8 border-l-2 border-indigo-600 pl-4">
              <span className="text-indigo-700 font-mono text-sm uppercase tracking-widest">Versão 2.0 Live</span>
              <div className="h-px w-8 bg-indigo-200"></div>
              <span className="text-slate-500 text-sm italic font-serif">Validado na Fazenda Cavalli</span>
            </div>

            <h1 className="text-6xl sm:text-7xl xl:text-8xl font-serif text-slate-900 leading-[0.95] tracking-tight mb-8">
              A ciência da <br />
              <span className="italic text-indigo-700">evolução</span> bovina.
            </h1>

            <p className="text-xl text-slate-600 max-w-xl leading-relaxed font-light font-sans">
              Não é apenas software. É um algoritmo de precisão que transforma índices genéticos complexos em decisões de acasalamento claras.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="flex flex-wrap gap-5 mt-4"
          >
            <button onClick={onCtaClick} className="px-8 py-4 bg-indigo-700 text-white text-lg hover:bg-slate-900 transition-all duration-300 rounded-sm shadow-xl shadow-indigo-900/10 flex items-center gap-3 group">
              Solicitar Acesso
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="px-8 py-4 bg-white border border-slate-300 text-slate-700 text-lg hover:bg-slate-50 hover:border-slate-400 transition-all rounded-sm">
              Ver Metodologia
            </button>
          </motion.div>

          <div className="flex items-center gap-8 mt-8 text-sm text-slate-500 font-mono">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-indigo-600" />
              <span>Rigor Científico</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-indigo-600" />
              <span>Integração ABS/CRV</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 relative h-[600px] hidden lg:block">
          <motion.div style={{ y: y1 }} className="absolute right-0 top-0 w-[90%] h-[80%] bg-slate-900 z-10 overflow-hidden shadow-2xl border-4 border-white">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
              </div>
              <span className="font-mono text-xs text-slate-500">analysis_module_v2.py</span>
            </div>
            <div className="p-8 font-mono text-sm space-y-4">
              <div className="flex justify-between text-indigo-400">
                <span>{'>'} TARGET_HERD</span>
                <span>500_COWS</span>
              </div>
              <div className="h-px w-full bg-slate-800 my-4"></div>
              <div className="space-y-2">
                <div className="flex justify-between text-slate-300">
                  <span>Inbreeding.coefficient</span>
                  <span className="text-green-400">2.4% [OPTIMAL]</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Milk_Production.projected</span>
                  <span>+12.5%</span>
                </div>
              </div>
              <div className="mt-12 p-4 bg-indigo-900/20 border border-indigo-500/30 text-indigo-200 text-xs leading-relaxed">
                ALGORITHM NOTE: Touro "Titanium" selecionado para Lote #4. Compatibilidade genealógica confirmada até 3ª geração.
              </div>
            </div>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500"></div>
          </motion.div>

          <motion.div style={{ y: y2 }} className="absolute left-0 bottom-10 w-[60%] bg-white p-8 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-slate-100 z-20">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-indigo-50 text-indigo-700 rounded-none border border-indigo-100">
                <Microscope size={24} />
              </div>
              <div>
                <h4 className="font-serif text-lg text-slate-900">Análise de Lote</h4>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Processando</p>
              </div>
            </div>
            <div className="flex items-end gap-1 h-16 mt-2">
              {[40, 70, 45, 90, 65, 80, 50].map((h, i) => (
                <motion.div
                  key={i}
                  initial={{ height: 0 }}
                  animate={{ height: `${h}%` }}
                  transition={{ duration: 1, delay: i * 0.1, repeat: Infinity, repeatType: "reverse", repeatDelay: 2 }}
                  className="flex-1 bg-slate-900"
                />
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const BentoGrid = () => {
  return (
    <section id="acasalamento" className="py-32 bg-white relative border-b border-slate-200">
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-end mb-20 gap-8">
          <div className="max-w-2xl">
            <h2 className="text-5xl font-serif text-slate-900 mb-6">Controle Total.<br />Sem Suposições.</h2>
            <p className="text-lg text-slate-600">
              Substituímos planilhas manuais e intuição por análise de dados robusta.
              Cada decisão é respaldada por milhares de pontos de dados genéticos.
            </p>
          </div>
          <div className="hidden md:block">
            <ArrowRight size={48} className="text-slate-200" strokeWidth={1} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 grid-rows-2 gap-0 border-t border-l border-slate-200">
          <div className="md:col-span-2 row-span-2 p-12 border-r border-b border-slate-200 hover:bg-slate-50 transition-colors group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
              <Dna size={200} />
            </div>
            <div className="relative z-10 h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 bg-indigo-900 text-white flex items-center justify-center mb-8">
                  <span className="font-serif text-xl italic">01</span>
                </div>
                <h3 className="text-3xl font-serif text-slate-900 mb-4">Algoritmo de Acasalamento</h3>
                <p className="text-slate-600 text-lg max-w-md leading-relaxed">
                  Nossa engine cruza o perfil genético de cada fêmea com catálogos inteiros (SelectSires, ABS).
                  O resultado não é apenas um touro, mas uma previsão da descendência.
                </p>
              </div>
              <div className="mt-12 flex gap-4">
                <div className="px-4 py-2 bg-green-100 text-green-800 text-sm font-mono border border-green-200">CONSANGUINIDADE &lt; 6%</div>
                <div className="px-4 py-2 bg-indigo-50 text-indigo-800 text-sm font-mono border border-indigo-100">DADOS IMPORTADOS</div>
              </div>
            </div>
          </div>
          <div className="p-10 border-r border-b border-slate-200 hover:bg-slate-50 transition-colors group">
            <ShieldCheck className="w-8 h-8 text-indigo-700 mb-6" />
            <h3 className="text-xl font-bold text-slate-900 mb-2">Proteção Genealógica</h3>
            <p className="text-slate-500 text-sm leading-relaxed">
              Análise profunda até o avô materno. O sistema alerta automaticamente (Verde/Amarelo/Vermelho) riscos genéticos.
            </p>
          </div>
          <div className="p-10 border-r border-b border-slate-200 hover:bg-slate-50 transition-colors group">
            <Activity className="w-8 h-8 text-indigo-700 mb-6" />
            <h3 className="text-xl font-bold text-slate-900 mb-2">Analytics em Lote</h3>
            <p className="text-slate-500 text-sm leading-relaxed">
              Otimize grupos de 60-70 vacas simultaneamente. O algoritmo equilibra o melhoramento genético com a praticidade do manejo.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

const TechnicalSpecs = () => {
  return (
    <section className="py-32 bg-slate-900 text-white relative overflow-hidden">
      <div className="absolute inset-0 opacity-20" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")` }}></div>
      <div className="max-w-[1400px] mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          <div>
            <h2 className="text-4xl md:text-6xl font-serif mb-10 leading-tight">
              Compatibilidade <br />
              <span className="text-indigo-400 italic">Universal</span>
            </h2>
            <div className="space-y-8">
              {[{ title: "Fontes de Dados", desc: "Importação nativa de Herd Dynamics, Catálogos PDF e Excel." }, { title: "Indicadores", desc: "Processamento de mais de 165 índices genéticos por animal." }, { title: "Infraestrutura", desc: "Arquitetura escalável pronta para rebanhos de alta performance." }].map((item, i) => (
                <div key={i} className="flex gap-6 border-b border-slate-800 pb-8 last:border-0">
                  <div className="font-mono text-indigo-400 text-xl">0{i + 1}</div>
                  <div>
                    <h4 className="text-xl font-bold mb-2">{item.title}</h4>
                    <p className="text-slate-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-slate-800 p-8 rounded-sm border border-slate-700 font-mono text-xs md:text-sm text-slate-300 shadow-2xl">
            <div className="flex gap-2 mb-6 border-b border-slate-700 pb-4">
              <div className="w-3 h-3 rounded-full bg-slate-600"></div>
              <div className="w-3 h-3 rounded-full bg-slate-600"></div>
              <span className="ml-auto opacity-50">import_log.txt</span>
            </div>
            <div className="space-y-3">
              <p><span className="text-green-400">[SUCCESS]</span> Connected to Herd Dynamics API</p>
              <p><span className="text-blue-400">[INFO]</span> Loading genetic markers for Lot #05...</p>
              <p><span className="text-yellow-400">[WARN]</span> Cow #402: High inbreeding risk (7.1%)</p>
              <p><span className="text-blue-400">[ACTION]</span> Re-routing: Suggesting 'Vortex' (0.5% Coeff)</p>
              <p><span className="text-green-400">[DONE]</span> Optimization complete.</p>
              <div className="h-4 w-4 bg-indigo-500 animate-pulse mt-4"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

const Footer = () => {
  return (
    <footer className="bg-white pt-32 pb-12 border-t border-slate-200">
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12 mb-24">
          <div>
            <span className="text-3xl font-serif font-bold tracking-tight text-slate-900 block mb-6">
              Genefy<span className="text-indigo-600">.</span>
            </span>
            <p className="text-slate-500 max-w-xs">
              Inteligência artificial aplicada ao melhoramento genético.<br /><br />
              Medianeira, PR — Brasil
            </p>
          </div>
          <div className="flex gap-20">
            <div>
              <h4 className="font-mono text-xs uppercase tracking-widest text-slate-400 mb-6">Plataforma</h4>
              <ul className="space-y-4 text-slate-900 font-medium">
                <li><a href="#" className="hover:text-indigo-600 transition-colors">Dashboard</a></li>
                <li><a href="#" className="hover:text-indigo-600 transition-colors">Tecnologia</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-mono text-xs uppercase tracking-widest text-slate-400 mb-6">Empresa</h4>
              <ul className="space-y-4 text-slate-900 font-medium">
                <li><a href="#" className="hover:text-indigo-600 transition-colors">Sobre</a></li>
                <li><a href="#" className="hover:text-indigo-600 transition-colors">Contato</a></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="border-t border-slate-100 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-400 font-mono">
          <p>&copy; 2025 Genefy Systems.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-slate-900">Privacy Policy</a>
            <a href="#" className="hover:text-slate-900">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

// --- Main Component ---

export default function GenefyLanding() {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <div className="bg-[#FDFBF9] min-h-screen font-sans text-slate-900 selection:bg-indigo-100 selection:text-indigo-900">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        :root { --font-serif: 'Playfair Display', serif; --font-sans: 'Inter', sans-serif; --font-mono: 'JetBrains Mono', monospace; }
        .font-serif { font-family: var(--font-serif); }
        .font-sans { font-family: var(--font-sans); }
        .font-mono { font-family: var(--font-mono); }
      `}</style>

      <NoiseOverlay />

      {/* Page Content */}
      <Navbar onLoginClick={() => setShowLogin(true)} />
      <Hero onCtaClick={() => setShowLogin(true)} />
      <BentoGrid />
      <TechnicalSpecs />
      <Footer />

      {/* Login Overlay */}
      <AnimatePresence>
        {showLogin && <LoginPage onBack={() => setShowLogin(false)} key="login-modal" />}
      </AnimatePresence>
    </div>
  );
}
