\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{xiaomi} % no versioning; versioning does not work well with arxiv.

%%======== Pckage options and base class ========
\RequirePackage{xifthen}
\newboolean{nonumbering}
\newboolean{logo}
\newboolean{address}
\newboolean{copyright}
\newboolean{internal}
\DeclareOption{nonumbering}{\setboolean{nonumbering}{false}}
\DeclareOption{logo}{\setboolean{logo}{true}}
\DeclareOption{address}{\setboolean{address}{true}}
\DeclareOption{copyright}{\setboolean{copyright}{true}}
\DeclareOption{internal}{\setboolean{internal}{false}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions\relax
\LoadClass{extarticle}

%%======== Packages Required ========
% Fonts and language
\AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
% JH: switched to xurl from url due to wrapping issues. This fixes it. For example, the Megatron-Turing NLG link
\RequirePackage{xurl}
\RequirePackage{hyperref}
\RequirePackage{pifont}
\RequirePackage[dvipsnames]{xcolor}
\RequirePackage{textcomp} % For copyright symbol styling
\RequirePackage[overload]{textcase}

%% *Graphics, tables and other formatting
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem} % For reducing bullet list item separation
\RequirePackage{tabularx}
\RequirePackage{datetime}

% Headers and footers
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{lastpage}  % Number of pages in the document

% Lists and their spacing
\RequirePackage{enumitem}
\setlist[itemize]{topsep=0pt}
\setlist[enumerate]{topsep=0pt}

% Title, Abstract, Bibliography
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}

%%======== Fonts ========

\RequirePackage{XCharter}
\RequirePackage[xcharter,bigdelims]{newtxmath}
\RequirePackage[scaled=1.1]{zlmtt}

\renewcommand{\sfdefault}{\rmdefault}


%%======== Margins and column spacing ========
\RequirePackage[left=2.5cm,%
right=2.5cm,%
top=3cm,%
bottom=3cm,%
headheight=40pt,%
headsep=20pt,%
a4paper]{geometry}%
\setlength{\columnsep}{15pt} % Distance between the two columns of text
\setlength{\parindent}{0pt} % remove indent
\setlength{\parskip}{0.5\baselineskip}
% Accommodate font-dependent line breaks without changing manuscript text.
\setlength{\emergencystretch}{1em}


\definecolor{micolor}{HTML}{F27423}
\newcommand{\micolor}[1]{{\bfseries\color[HTML]{F27423} #1}}

%% Custom font sizes and styles
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\titlefont}{\color{black}\normalfont\sffamily\bfseries\fontsize{18}{18}\selectfont}

\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{blue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{11}{12}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{black}\bfseries\fontsize{13}{14}\selectfont}

\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newtoks\correspondingauthor
\newtoks\paperurl
\newtoks\reportnumber

% Dates and Times for footer
% ISO-8601 date format
\newdateformat{monthyeardate}{\THEYEAR-\THEMONTH-\THEDAY}

\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{2}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

%%========  Author and affiliation ========
\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\renewcommand\Authfont{\normalfont\sffamily\fontsize{11}{15}\selectfont\centering}
\renewcommand\Affilfont{\bfseries\fontsize{13}{15}\selectfont\centering}
\makeatletter
\renewcommand\AB@affilsepx{ , \protect\Affilfont}
\makeatother
\renewcommand\Authands{, }

\newcommand{\internalonly}{Xiaomi, Confidential. Internal Only.}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} Xiaomi. All rights reserved}


%%======== Header and Footer Content ========
% Header and Footer for the first page

\fancypagestyle{firststyle}{
    % left side of the header
    \fancyhead[L]{
        \ifthenelse{\boolean{logo}}{
            \raisebox{1.5pt}{\includegraphics[height=11pt]{xiaomi/mimo_logo}}
        }{}
        \ifdefined\paperurl
        \if\relax\the\paperurl\relax \else
            \href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\ \fi
        \else \fi
    }

    % center of the header
    \fancyhead[C]{}

    % right side of the header
    \fancyhead[R]{
        \ifthenelse{\boolean{logo}}{
            \raisebox{-0.5pt}{\includegraphics[height=23pt]{xiaomi/xiaomi_logo}}
        }{}
    }

    % remove the page number of the first page
    \fancyfoot[C]{\footerfont\bfseries\relax}
}

% Header and Footer for pages from 2 onwards
\fancyhead[L,R]{}
\makeatletter
\fancyhead[C]{\footerfont MiMo-7B: Technical Report}

\makeatother
\fancyfoot[C]{}
\fancyfoot[L]{}
\fancyfoot[C]{\footerfont \thepage}

% Header and footer rules (coloured).
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

\renewenvironment{abstract}
{\par\noindent\\  \ignorespaces \bfseries}
{\par\bigskip}

%%======== Table of contents formatting ========
\makeatletter
\renewcommand\tableofcontents{
    \begingroup
      \sffamily
      \@ifstar{
          \@starttoc{toc}
      }{
          \section*{\contentsname}
          \@starttoc{toc}
      }
    \endgroup
}

%%======== Abstract and section formatting ========
\def\xabstract{abstract}
\long\def\abstract#1\end#2{\def\two{#2}\ifx\two\xabstract
	\long\gdef\theabstract{\ignorespaces#1}
	\def\go{\end{abstract}}\else
\typeout{^^J^^J PLEASE DO NOT USE ANY \string\begin\space \string\end^^J
	COMMANDS WITHIN ABSTRACT^^J^^J}#1\end{#2}
\gdef\theabstract{\vskip12pt BADLY FORMED ABSTRACT: PLEASE DO
NOT USE {\tt\string\begin...\string\end} COMMANDS WITHIN
THE ABSTRACT\vskip12pt}\let\go\relax\fi
\go}

% Define an environment with abstract content and styling
\makeatletter
\newcommand{\abscontent}{
	\noindent
        \centerline{\sffamily\fontsize{13pt}{14pt}\selectfont\textbf{Abstract}}\vspace{5ex}
	\parbox{\dimexpr\linewidth}{\absfont \theabstract}
	\@ifundefined{@keywords}{}{
		\vskip1em \noindent \keywordsfont  Keywords: \@keywords}
}

\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
        \vspace*{3pt}
	\begin{adjustwidth}{0pt}{0pt}
		\begin{flushleft}
			{
				{\raggedright \titlefont \@title\par}
				\vskip20pt
				{\raggedright \@author\par}
				\vskip30pt
			}
		\end{flushleft}
	\end{adjustwidth}
	\egroup
	{
		{\abscontent}
	}
	\thispagestyle{firststyle}
}
\makeatother

%%========  Bibliography using bibtex ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}

\newcommand{\sectionfont}
{\fontsize{12}{10}\selectfont}

\newcommand{\subsectionfont}
{\fontsize{11.5}{10}\selectfont}

\newcommand{\subsubsectionfont}
{\fontsize{10.7}{10}\selectfont}

\titleformat{\section}
{\sffamily\sectionfont\bfseries\headingfont}
{\thesection}
{1.0em}
{#1}
[]

\titleformat{name=\section,numberless}
{\sffamily\sectionfont\bfseries\headingfont}
{}
{0em}
{#1}
[]

\titleformat{\subsection}
{\sffamily\subsectionfont\bfseries}
{\thesubsection}
{1.0em}
{#1}
[]

\titleformat{\subsubsection}
{\sffamily\subsubsectionfont\bfseries}
{\thesubsubsection}
{1.0em}
{#1}
[]

\titleformat{\paragraph}[runin]
{\sffamily\small\bfseries}
{\theparagraph}
{1.0em}
{#1}
[]

\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}
\titlespacing{\paragraph}{0pc}{2ex plus2pt minus1pt}{1em}

%%======== Captions in tables and figures ========
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\textbf{#1 #2}} #3}
\captionsetup{
figurename=Figure,
labelsep=custom,
singlelinecheck=true,
format=custom,
}
