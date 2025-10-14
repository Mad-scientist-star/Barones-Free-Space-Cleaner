import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { HardDrive, Trash2, Shield, Download, Github, CheckCircle2, Package, Terminal } from 'lucide-react'
import './App.css'
import logo1 from './assets/logos/logo_concept_1.png'
import logo2 from './assets/logos/logo_concept_2.png'
import logo3 from './assets/logos/logo_concept_3.png'
import logo4 from './assets/logos/logo_concept_4.png'
import logo5 from './assets/logos/logo_concept_5.png'

function App() {
  const [selectedLogo, setSelectedLogo] = useState(1)
  
  const logos = [
    { id: 1, src: logo1, name: 'Concept 1' },
    { id: 2, src: logo2, name: 'Concept 2' },
    { id: 3, src: logo3, name: 'Concept 3' },
    { id: 4, src: logo4, name: 'Concept 4' },
    { id: 5, src: logo5, name: 'Concept 5' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src={logos[selectedLogo - 1].src} 
              alt="Barones Logo" 
              className="h-12 w-12 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-slate-900">Barones Free Space Cleaner</h1>
              <p className="text-sm text-slate-600">Secure Data Deletion for Linux</p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm" asChild>
              <a href="https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner" target="_blank" rel="noopener noreferrer">
                <Github className="h-4 w-4 mr-2" />
                GitHub
              </a>
            </Button>
            <Button size="sm" asChild>
              <a href="#downloads">
                <Download className="h-4 w-4 mr-2" />
                Download
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-4">
              For Linux Only
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
              Actually Delete Files From Your Drive
            </h2>
            <p className="text-lg text-slate-700 mb-8">
              When you "delete" a file, it's not really gone. Barones Free Space Cleaner writes different patterns to all the free space on your drives, then deletes it. Simple. Effective. No extra bullshit.
            </p>
            <div className="flex gap-4">
              <Button size="lg" asChild>
                <a href="#install">
                  <Download className="h-5 w-5 mr-2" />
                  Get Started
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner" target="_blank" rel="noopener noreferrer">
                  View on GitHub
                </a>
              </Button>
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-2xl p-8 border border-slate-200">
            <img 
              src={logos[selectedLogo - 1].src} 
              alt="Barones Logo" 
              className="w-full max-w-md mx-auto"
            />
          </div>
        </div>
      </section>

      {/* Why Section */}
      <section className="bg-white py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h3 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              Why Barones?
            </h3>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              The truth about file deletion and why you need this tool
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 className="h-8 w-8 text-red-600" />
              </div>
              <h4 className="text-xl font-bold text-slate-900 mb-3">Fake Deletion</h4>
              <p className="text-slate-600">
                When you delete a file, the operating system just removes the reference to it. The actual data remains on your drive until it's overwritten.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <HardDrive className="h-8 w-8 text-yellow-600" />
              </div>
              <h4 className="text-xl font-bold text-slate-900 mb-3">Data Recovery</h4>
              <p className="text-slate-600">
                Anyone with recovery tools can potentially access your "deleted" files. This is a privacy and security risk, especially when selling or donating drives.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <h4 className="text-xl font-bold text-slate-900 mb-3">True Deletion</h4>
              <p className="text-slate-600">
                Barones overwrites free space with zeros, ones, random data, or custom patterns, making recovery impossible. Your data is truly gone.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="text-center mb-12">
          <h3 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            Simple. Powerful. Effective.
          </h3>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            No complicated settings. Just easy-to-understand buttons that do what they say.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
            <CheckCircle2 className="h-8 w-8 text-blue-600 mb-4" />
            <h4 className="text-xl font-bold text-slate-900 mb-3">Multiple Wipe Patterns</h4>
            <p className="text-slate-600">
              Choose from zeros, ones, random data, or the 3487 pattern. Cycle through patterns automatically for thorough wiping.
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
            <CheckCircle2 className="h-8 w-8 text-blue-600 mb-4" />
            <h4 className="text-xl font-bold text-slate-900 mb-3">Drive Health Monitoring</h4>
            <p className="text-slate-600">
              Built-in SMART data monitoring for both SATA/SSD and NVMe drives. Check temperature, wear level, and overall health.
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
            <CheckCircle2 className="h-8 w-8 text-blue-600 mb-4" />
            <h4 className="text-xl font-bold text-slate-900 mb-3">Progress Tracking</h4>
            <p className="text-slate-600">
              Real-time write speed and estimated time remaining. Pause, resume, or cancel operations at any time.
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border border-slate-200">
            <CheckCircle2 className="h-8 w-8 text-blue-600 mb-4" />
            <h4 className="text-xl font-bold text-slate-900 mb-3">Clean GTK3 Interface</h4>
            <p className="text-slate-600">
              Native Linux desktop application with a straightforward interface. No bloat, no confusion, just the tools you need.
            </p>
          </div>
        </div>
      </section>

      {/* Downloads Section */}
      <section id="downloads" className="container mx-auto px-4 py-16 md:py-24">
        <div className="text-center mb-12">
          <h3 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            Download & Install
          </h3>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Choose your Linux distribution and install with a single command
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-12">
          {/* Debian/Ubuntu */}
          <div className="bg-white rounded-xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="h-8 w-8 text-orange-600" />
            </div>
            <h4 className="text-2xl font-bold text-slate-900 mb-2 text-center">Debian/Ubuntu</h4>
            <p className="text-slate-600 text-center mb-6">For Debian, Ubuntu, Linux Mint, and derivatives</p>
            <div className="space-y-4">
              <Button className="w-full" asChild>
                <a href="/downloads/barones-free-space-cleaner_1.0.1_all.deb" download>
                  <Download className="h-4 w-4 mr-2" />
                  Download .deb
                </a>
              </Button>
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-xs text-slate-600 mb-2">Install with:</p>
                <code className="text-xs text-slate-800 block">sudo dpkg -i barones-free-space-cleaner_1.0.1_all.deb</code>
              </div>
            </div>
          </div>

          {/* Fedora/RHEL */}
          <div className="bg-white rounded-xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="h-8 w-8 text-blue-600" />
            </div>
            <h4 className="text-2xl font-bold text-slate-900 mb-2 text-center">Fedora/RHEL</h4>
            <p className="text-slate-600 text-center mb-6">For Fedora, RHEL, CentOS, and derivatives</p>
            <div className="space-y-4">
              <Button className="w-full" asChild>
                <a href="/downloads/barones-free-space-cleaner-1.0.1-1.noarch.rpm" download>
                  <Download className="h-4 w-4 mr-2" />
                  Download .rpm
                </a>
              </Button>
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-xs text-slate-600 mb-2">Install with:</p>
                <code className="text-xs text-slate-800 block">sudo rpm -i barones-free-space-cleaner-1.0.1-1.noarch.rpm</code>
              </div>
            </div>
          </div>

          {/* Arch Linux */}
          <div className="bg-white rounded-xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="w-16 h-16 bg-cyan-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Terminal className="h-8 w-8 text-cyan-600" />
            </div>
            <h4 className="text-2xl font-bold text-slate-900 mb-2 text-center">Arch Linux</h4>
            <p className="text-slate-600 text-center mb-6">For Arch Linux and Manjaro</p>
            <div className="space-y-4">
              <Button className="w-full" variant="outline" asChild>
                <a href="https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner/tree/main/packaging/aur" target="_blank" rel="noopener noreferrer">
                  <Github className="h-4 w-4 mr-2" />
                  View AUR Files
                </a>
              </Button>
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-xs text-slate-600 mb-2">Install with yay:</p>
                <code className="text-xs text-slate-800 block">yay -S barones-free-space-cleaner</code>
                <p className="text-xs text-slate-500 mt-2">Available on the AUR</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 max-w-3xl mx-auto">
          <h4 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-blue-600" />
            What happens after installation?
          </h4>
          <p className="text-slate-700 mb-3">
            The package installer will automatically:
          </p>
          <ul className="text-slate-700 space-y-2 ml-6">
            <li>• Install the application to <code className="bg-white px-2 py-1 rounded text-sm">/usr/bin</code></li>
            <li>• Add a desktop entry to your Applications menu</li>
            <li>• Install the application icon in multiple sizes</li>
            <li>• Set up all required dependencies</li>
          </ul>
          <p className="text-slate-700 mt-4">
            After installation, you'll find <strong>"Barones Free Space Cleaner"</strong> in your Applications menu under System or Utilities.
          </p>
        </div>
      </section>



      {/* Logo Selection Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="text-center mb-12">
          <h3 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            Logo Concepts
          </h3>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Click on a logo to preview it throughout the site
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 max-w-5xl mx-auto">
          {logos.map((logo) => (
            <button
              key={logo.id}
              onClick={() => setSelectedLogo(logo.id)}
              className={`bg-white rounded-xl p-6 border-2 transition-all hover:shadow-lg ${
                selectedLogo === logo.id 
                  ? 'border-blue-600 shadow-lg scale-105' 
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <img 
                src={logo.src} 
                alt={logo.name} 
                className="w-full aspect-square object-contain mb-3"
              />
              <p className="text-sm font-medium text-slate-700">{logo.name}</p>
            </button>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <img 
                src={logos[selectedLogo - 1].src} 
                alt="Barones Logo" 
                className="h-10 w-10 object-contain"
              />
              <div>
                <p className="font-bold">Barones Free Space Cleaner</p>
                <p className="text-sm text-slate-400">Open source data deletion tool</p>
              </div>
            </div>
            <div className="flex gap-6">
              <a 
                href="https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white transition-colors"
              >
                <Github className="h-6 w-6" />
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-slate-800 text-center text-slate-400 text-sm">
            <p>© 2025 Barones Free Space Cleaner. Open source software for Linux.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

