# TODO:
#	- finish it
#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	smp		# don't build SMP module
%bcond_without	userspace	# don't build userspace module
%bcond_with	verbose		# verbose build (V=1)
#
Summary:	UNH iSCSI Initiator/Target for Linux
Summary(pl):	Sterowniki UNH iSCSI Initiator/Target dla Linuksa
Name:		unh_iscsi
Version:	1.6.00
%define		_rel 1
Release:	%{_rel}
License:	GPL
Group:		Base/Kernel
Source0:	http://dl.sourceforge.net/unh-iscsi/%{name}-%{version}.tar.gz
# Source0-md5:	086e09a2cb48f0020ff6602aa5e34cf4
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Patch0:		%{name}-headers.patch
URL:		http://unh-iscsi.sourceforge.net/
%{?with_dist_kernel:BuildRequires:	kernel-headers >= 2.6.0}
BuildRequires:	sysfsutils-static
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sbindir	/sbin

%description
The UNH-iSCSI project consists of software implementations of an
Initiator and Target emulator loadable modules for the IETF Networking
(SAN) protocol (Draft 20).

%description -l pl
Projekt UNH-iSCSI sk³ada siê z programowych implementacji emulacji
Initiator i Target jako ³adowalnych modu³ów dla protoko³u IETF
Networking (SAN) (draft 20).

%package -n kernel-unh_iscsi
Summary:	UNH ISCSI kernel module
Summary(pl):	Modu³ j±dra UNH ISCSI
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}

%description -n kernel-unh_iscsi
IP over SCSI kernel module.

%description -n kernel-unh_iscsi -l pl
Modu³ j±dra dla protoko³u IP over SCSI.

%package -n kernel-smp-unh_iscsi
Summary:	ISCSI SMP kernel module
Summary(pl):	Modu³ j±dra SMP ISCSI
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}

%description -n kernel-smp-unh_iscsi
IP over SCSI SMP kernel module.

%description -n kernel-smp-unh_iscsi -l pl
Modu³ j±dra SMP dla protoko³u IP over SCSI.

%prep
%setup -q -n %{name}.%{version}
%patch0 -p1

%build
cd src
cp Makefile-26 Makefile

%if %{with kernel}
echo "#define OUR_NAME \"PLD Linux %{name}/%{version} for kernel %{_kernel_ver_str}.\"" > initiator/version.h

# kernel module(s)
for cfg in %{?with_dist_kernel:%{?with_smp:smp} up}%{!?with_dist_kernel:nondist}; do
	if [ ! -r "%{_kernelsrcdir}/config-$cfg" ]; then
		exit 1
	fi
	rm -rf include
	install -d include/{linux,config}
	ln -sf %{_kernelsrcdir}/config-$cfg .config
	ln -sf %{_kernelsrcdir}/include/linux/autoconf-$cfg.h include/linux/autoconf.h
	ln -sf %{_kernelsrcdir}/include/asm-%{_target_base_arch} include/asm
	ln -sf %{_kernelsrcdir}/Module.symvers-$cfg Module.symvers
	touch include/config/MARKER

	%{__make} -C %{_kernelsrcdir} clean \
		RCS_FIND_IGNORE="-name '*.ko' -o" \
		M=$PWD O=$PWD \
		%{?with_verbose:V=1}
		%{__make} -C %{_kernelsrcdir} modules \
		M=$PWD O=$PWD \
		%{?with_verbose:V=1}
	
	for mod in unh_iscsi_initiator unh_iscsi_target unh_scsi_target; do
		mv ${mod}{,-$cfg}.ko
	done
done
%endif

%{__make} -C cmd \
	CC="%{__cc}" \
	CFLAGS="%{rpmcflags}"

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sbindir},%{_mandir}/man{1,5,8},/etc/{rc.d/init.d,sysconfig}}

cd src
%if %{with kernel}
install -d $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}{,smp}/misc
for mod in unh_iscsi_initiator unh_iscsi_target unh_scsi_target; do
	install ${mod}-%{?with_dist_kernel:up}%{!?with_dist_kernel:nondist}.ko \
		$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}/misc/${mod}.ko
%if %{with smp} && %{with dist_kernel}
	install ${mod}-smp.ko \
		$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}smp/misc/${mod}.ko
%endif
done
%endif

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
install %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/%{name}

install cmd/{iscsi_config,iscsi_connect,iscsi_disconnect,iscsi_manage,iscsi_mount,iscsi_rebuild,iscsi_test,iscsi_umount} \
	$RPM_BUILD_ROOT%{_sbindir}

%clean
rm -rf $RPM_BUILD_ROOT

%post -n kernel-unh_iscsi
%depmod %{_kernel_ver}

%postun -n kernel-unh_iscsi
%depmod %{_kernel_ver}

%post -n kernel-smp-unh_iscsi
%depmod %{_kernel_ver}smp

%postun -n kernel-smp-unh_iscsi
%depmod %{_kernel_ver}smp

%post
/sbin/chkconfig --add %{name}
#if [ -f /var/lock/subsys/%{name} ]; then
#	/etc/rc.d/init.d/%{name} restart 1>&2
#else
#	echo "Type \"/etc/rc.d/init.d/%{name} start\" to start %{name}" 1>&2
#fi

%preun
if [ "$1" = "0" ]; then
#	if [ -f /var/lock/subsys/%{name} ]; then
#		/etc/rc.d/init.d/%{name} stop >&2
#	fi
	/sbin/chkconfig --del %{name}
fi

%if %{with userspace}
%files
%defattr(644,root,root,755)
%doc src/docs/* src/CHANGELOG
%attr(755,root,root) %{_sbindir}/*
%attr(754,root,root) /etc/rc.d/init.d/%{name}
%attr(640,root,root) %config(noreplace) %verify(not mtime md5 size) /etc/sysconfig/%{name}
%endif

%if %{with kernel}
%files -n kernel-unh_iscsi
%defattr(644,root,root,755)
%attr(644,root,root) /lib/modules/%{_kernel_ver}/misc/*

%if %{with smp} && %{with dist_kernel}
%files -n kernel-smp-unh_iscsi
%defattr(644,root,root,755)
%attr(644,root,root) /lib/modules/%{_kernel_ver}smp/misc/*
%endif
%endif
