.PHONY: install
install:
	@cp network_monitor.py /usr/local/bin/
	@cp config.yaml /etc/default/network-monitor.yaml
	@sed -ri "s/__USER__/$(SUDO_USER)/g" /etc/default/network-monitor.yaml
	@cp network_monitor.service /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable network_monitor.service
	@echo "Finished installation."
	@echo "Please configure/verify the user in /etc/default/network-monitor.yaml"
	@echo "Service will run at the next boot; to start manually, run"
	@echo "systemctl start network_monitor.service"

.PHONY: uninstall
uninstall:
	@rm -f /usr/local/bin/network_monitor.py
	@rm -f /etc/default/network-monitor.yaml
	@rm -f /etc/systemd/system/network_monitor.service
	@systemctl daemon-reload
