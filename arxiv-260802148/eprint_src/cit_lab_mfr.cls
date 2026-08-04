%%======== Pckage options and base class ========
%\newboolean{logo}
\usepackage[table,dvipsnames]{xcolor}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{bytedance_seed}
\LoadClassWithOptions{article}
% \pdfoutput=1

% --- ADDED: Package for Times New Roman font ---
% This one package sets the main text and math fonts to Times.
\RequirePackage{newtxtext, newtxmath}
% Layout
\RequirePackage[top=2.75cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
% \RequirePackage{ulem}  % 引用下划线
% \DisableLigatures[f]{family=sf*}
\RequirePackage{graphicx}
\RequirePackage{subcaption}

\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}
\RequirePackage[most]{tcolorbox}
% \RequirePackage{xcolor}
\definecolor{seedbg}{HTML}{18398D}
\definecolor{fudanblue}{HTML}{18398D}
\definecolor{myblue}{RGB}{210, 225, 255}
\definecolor{lightred}{RGB}{255, 182, 193}
\definecolor{lightgreen}{RGB}{144, 238, 144}
\definecolor{lightblue}{RGB}{173, 216, 230}
\definecolor{lightergray}{gray}{0.98}
\definecolor{lighterblue}{RGB}{240, 250, 250}

\newcommand{\fudanblue}[1]{{\bfseries\color[HTML]{18398D} #1}}

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=fudanblue,
  citecolor=fudanblue,
  urlcolor=fudanblue
}

\RequirePackage[numbers, sort&compress]{natbib}
%\RequirePackage[round,authoryear]{natbib}
\def\bibfont{\small}

%%========  Bibliography using bibtex ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}

% Section and caption format
\newcommand{\sectionfont}
{\fontsize{12}{10}\selectfont}

\newcommand{\subsectionfont}
{\fontsize{11}{10}\selectfont}

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\sectionfont\rmfamily\bfseries\fudanblue}
\titleformat*{\subsection}{\subsectionfont\rmfamily\bfseries\fudanblue}
\titleformat*{\subsubsection}{\normalsize\rmfamily\bfseries\fudanblue}


\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}

\DeclareCaptionFormat{custom}{{\rmfamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand{\authorfont}
{\fontsize{12}{14}\selectfont}
%作者设置
\newcommand\authorlist{}

\newcommand\authorformat[2][]{\authorfont {\rmfamily\bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand{\affiliationfont}
{\fontsize{10}{12}\selectfont}

\newcommand\affiliationlist{}
% MODIFIED: Replaced custom font with \rmfamily
\newcommand\affiliationformat[2][]{{\affiliationfont {\rmfamily $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand{\contributionfont}
{\fontsize{10}{12}\selectfont}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand{\checkdatafont}
{\fontsize{7.92}{10}\selectfont}

\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont\rmfamily \bfseries #1:} #2}} 
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}

\newcommand{\abstractinfont}
{\fontsize{10}{12}\selectfont}

\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\checkdata[Date]{#1}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}

\newcommand{\titlefont}
{\fontsize{17}{20}\selectfont}

\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\rmfamily #1}}}

\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont}


\newcommand{\beginabstract}{\abstractfont{\rmfamily\bfseries \fudanblue{Abstract}\par}}


\newcommand{\beginappendix}{\appendix{\titlefont\rmfamily \fudanblue{Appendix}\par}}

\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % 目录后一行连续的点

\renewcommand{\cftsecfont}{\rmfamily}

\renewcommand{\cftsecpagefont}{\rmfamily}{\color{fudanblue}}
\renewcommand{\cfttoctitlefont}
{\rmfamily\sectionfont\fudanblue} 


\fancypagestyle{firststyle}{
    \fancyhead[L]{
        \vskip 4mm
        \begin{tabular}{@{}c@{}c@{}c@{}}
            \includegraphics[height=1cm]{figures/logo.pdf} & 
            % \hspace{2mm}\includegraphics[height=1cm]{images/logo.jpg} & 
            % \hspace{2mm}\raisebox{0.25cm}{\sffamily\Large ByteDance}
        \end{tabular}
    }
    \fancyhead[C]{}
    \fancyhead[R]{}
}


%去除页眉页脚横线
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% rules for title box at top of first page
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%此处为标题两侧线段
\newcommand{\@toptitlebar}{
  \fudanblue{\hrule height 0.7pt }
  \vskip 6mm
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  %\vskip -\parskip
  \fudanblue{\hrule height 0.7pt}
  %\vskip 0.09in%
}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\mymaketitle}{%
  %\tcbset{enhanced,frame hidden}
  \tcbset{enhanced}
  \tcbset{left=8mm}
  \tcbset{right=8mm}
  \tcbset{top=6mm}
  \tcbset{bottom=6mm}
  \tcbset{colback=white}
   % 框线颜色
  \tcbset{colframe=seedbg}
  % 调整框线粗细
  \tcbset{boxrule=0.5pt}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \tcbset{arc=2.5mm}
       {
       \setlength{\parskip}{0mm}
       \centering
       \nohyphens
       %

       {
       \@toptitlebar

         \titlelist\par
          \@bottomtitlebar
       }
       \vskip 6mm
       \authorlist
       \vskip 3mm
       %
       \affiliationlist\par
       \vskip 3mm
       %
       \contributionlist\par
     }
    \vskip 6mm

\begin{tcolorbox}[
  colback=lighterblue!50,
  overlay={
    % \node[
    %   anchor=south east,         % 将节点的右下角作为锚点
    %   at=(frame.south east),     % 定位到盒子的右下角
    %   xshift=-3mm,               % 向左偏移，留出边距
    %   yshift=3mm                 % 向上偏移，留出边距
    % ] {\includegraphics[height=1cm]{images/logo_with_name.jpeg}}; % 插入你的logo
  }
]
  \setlength{\parindent}{0cm}
  \setlength{\parskip}{0cm}

  \begin{center}
      \beginabstract
      \vskip 3mm
  \end{center}

  \abstractlist\par
  ~
  
  {
    \setlength{\parskip}{0cm}
    \ifdefempty{\checkdatalist}{\vspace*{0.65cm}}{\checkdatalist\par}
  }
\end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier

  %加入页眉页脚
  \thispagestyle{firststyle}

}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
  \vskip 3mm
  \mymaketitle
  \vskip 8mm
]
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
  \vskip 8mm
  %\setlength{\parskip}{4mm}
}%
\fi